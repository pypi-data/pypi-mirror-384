# SPDX-FileCopyrightText: 2025-present Ryo Kuroiwa <kuroiwa@nii.ac.jp>
#
# SPDX-License-Identifier: MIT

from abc import abstractmethod
import copy
import math
import time
import random

import pyscipopt as scip


class EdgeConsdata:
    def __init__(self, edge, node):
        self.edge = edge
        self.propagated = False
        self.npropagated = 0
        self.node = node


class EdgeConshdlr(scip.Conshdlr):
    def __init__(self):
        self.conss = []

    def consdata_create(self, name, edge, node):
        cons = self.model.createCons(
            conshdlr=self,
            name=name,
            initial=False,
            separate=False,
            enforce=False,
            check=False,
            propagate=True,
            local=True,
            modifiable=False,
            dynamic=False,
            removable=False,
            stickingatnode=True,
        )
        cons.data = EdgeConsdata(edge, node)
        self.conss.append(cons)

        return cons

    def consactive(self, constraint):
        if constraint.data.npropagated != len(self.model.data["y"]):
            constraint.data.propagated = False
            self.model.repropagateNode(constraint.data.node)

    def consdeactive(self, constraint):
        constraint.data.npropagated = len(self.model.data["y"])

    def consprop(self, constraints, _nusefulconss, _nmarkedconss, _proptiming):
        result = scip.SCIP_RESULT.DIDNOTFIND

        for c in constraints:
            if (
                c.data.propagated
                or c.data.edge not in self.model.data["edge_to_route_indices"]
            ):
                continue

            if self.model.data["verbosity"] >= 3:
                print(
                    "Edge: {} disabled at node {}".format(
                        c.data.edge, self.model.getCurrentNode().getNumber()
                    )
                )

            for i in self.model.data["edge_to_route_indices"][c.data.edge]:
                infeasible, _ = self.model.fixVar(
                    self.model.getTransformedVar(self.model.data["y"][i]), 0
                )

                if infeasible:
                    return {"result": scip.SCIP_RESULT.CUTOFF}

            c.data.propagated = True
            c.data.npropagated = len(self.model.data["y"])

            if result == scip.SCIP_RESULT.DIDNOTFIND:
                result = scip.SCIP_RESULT.REDUCEDDOM

        return {"result": result}


class EdgeBranchrule(scip.Branchrule):
    def branchexeclp(self, _allowaddcons):
        branch_vars, sol_vals, *_ = self.model.getLPBranchCands()

        edge_to_val = {}

        for i, var in enumerate(branch_vars):
            r = self.model.data["routes"][VRPBaP.var_to_index(var)]

            for edge in zip(r[:-1], r[1:]):
                if edge not in edge_to_val:
                    edge_to_val[edge] = 0

                edge_to_val[edge] += sol_vals[i]

        chosen_edge, _ = max(
            edge_to_val.items(),
            key=lambda x: min(x[1] - math.floor(x[1]), math.ceil(x[1]) - x[1]),
        )

        if self.model.data["verbosity"] >= 2:
            print(
                "At node {}, branching on edge: {} ".format(
                    self.model.getCurrentNode().getNumber(), chosen_edge
                )
            )

        left_child = self.model.createChild(0, self.model.getLocalEstimate())
        left_id = left_child.getNumber()
        left_cons = self.model.data["conshdlr"].consdata_create(
            str((left_id, chosen_edge)), chosen_edge, left_child
        )
        self.model.addConsNode(left_child, left_cons)

        right_child = self.model.createChild(0, self.model.getLocalEstimate())
        right_id = right_child.getNumber()

        for edge in self.model.data["edge_to_replacing_edges"][chosen_edge]:
            right_cons = self.model.data["conshdlr"].consdata_create(
                str((right_id, edge)), edge, right_child
            )
            self.model.addConsNode(right_child, right_cons)

        return {"result": scip.SCIP_RESULT.BRANCHED}

    def branchexecps(self, _allowaddcons):
        branch_vars, *_ = self.model.getPseudoBranchCands()

        edge_to_val = set()

        for var in branch_vars:
            r = self.model.data["routes"][VRPBaP.var_to_index(var)]

            for edge in zip(r[:-1], r[1:]):
                edge_to_val.add(edge)

        edge_to_val = list(edge_to_val)
        chosen_edge = random.choice(edge_to_val)

        if self.model.data["verbosity"] >= 2:
            print(
                "At node {}, branching on edge: {} ".format(
                    self.model.getCurrentNode().getNumber(), chosen_edge
                )
            )

        left_child = self.model.createChild(0, self.model.getLocalEstimate())
        left_id = left_child.getNumber()
        left_cons = self.model.data["conshdlr"].consdata_create(
            str((left_id, chosen_edge)), chosen_edge, left_child
        )
        self.model.addConsNode(left_child, left_cons)

        right_child = self.model.createChild(0, self.model.getLocalEstimate())
        right_id = right_child.getNumber()

        for edge in self.model.data["edge_to_replacing_edges"][chosen_edge]:
            right_cons = self.model.data["conshdlr"].consdata_create(
                str((right_id, edge)), edge, right_child
            )
            self.model.addConsNode(right_child, right_cons)

        print("WARNING: branching on pseudosolution")

        return {"result": scip.SCIP_RESULT.BRANCHED}


class VRPBaP:
    def __init__(
        self,
        nodes,
        edges,
        start_depots,
        end_depots,
        pricer,
        routes=None,
        route_coeffs=None,
        route_costs=None,
        max_routes=None,
        time_limit=None,
        verbosity=0,
        objective_integral=False,
        checkpriority=1000000,
        propfreq=1,
        edge_branch_priority=1000000,
        mip_gap=1e-6,
    ):
        self.started = time.perf_counter()

        routes = [] if routes is None else routes
        route_coeffs = [] if route_coeffs is None else route_coeffs
        route_costs = [] if route_costs is None else route_costs
        self.model = self.create_model(
            nodes, route_coeffs, route_costs, max_routes=max_routes
        )
        self.model.includePricer(
            pricer, "RoutePricer", "Pricer to generate routes", delay=True
        )

        edge_to_route_indices = {}

        for i, r in enumerate(routes):
            for edge in zip(r[:-1], r[1:]):
                if edge not in edge_to_route_indices:
                    edge_to_route_indices[edge] = []

                edge_to_route_indices[edge].append(i)

        node_to_destinations = {}
        node_to_sources = {}

        for i, j in edges:
            if i not in node_to_destinations:
                node_to_destinations[i] = []

            if j not in node_to_sources:
                node_to_sources[j] = []

            node_to_destinations[i].append(j)
            node_to_sources[j].append(i)

        edge_to_replacing_edges = {e: [] for e in edges}

        for i, j in edges:
            if i not in start_depots:
                for k in node_to_destinations[i]:
                    if k != j:
                        edge_to_replacing_edges[i, j].append((i, k))

            if j not in end_depots:
                for k in node_to_sources[j]:
                    if k != i:
                        edge_to_replacing_edges[i, j].append((k, j))

        self.model.data["max_routes"] = max_routes
        self.model.data["nodes"] = nodes
        self.model.data["edges"] = edges
        self.model.data["routes"] = routes
        self.model.data["edge_to_route_indices"] = edge_to_route_indices
        self.model.data["edge_to_replacing_edges"] = edge_to_replacing_edges
        self.model.data["verbosity"] = verbosity

        conshdlr = EdgeConshdlr()
        self.model.includeConshdlr(
            conshdlr,
            "EdgeConshdlr",
            "Conshdlr disabling edges",
            chckpriority=checkpriority,
            propfreq=propfreq,
        )
        self.model.data["conshdlr"] = conshdlr

        branchrule = EdgeBranchrule()
        self.model.includeBranchrule(
            branchrule,
            "EdgeBranchrule",
            "Branchrule disabling edges",
            priority=edge_branch_priority,
            maxdepth=-1,
            maxbounddist=1,
        )

        if verbosity == 0:
            self.model.hideOutput()

        self.model.setParam("display/freq", 1)
        self.model.setParam("display/headerfreq", 1)

        if time_limit is not None:
            self.model.setParam("limits/time", time_limit)

        self.model.data["has_time_limit"] = time_limit is not None

        self.model.setParam("limits/gap", mip_gap)

        if objective_integral:
            self.model.setObjIntegral()

        self.model.setPresolve(scip.SCIP_PARAMSETTING.OFF)
        self.model.setSeparating(scip.SCIP_PARAMSETTING.OFF)
        self.model.setIntParam("propagating/rootredcost/freq", -1)

    def create_model(
        self,
        nodes,
        route_coeffs,
        route_costs,
        max_routes=None,
    ):
        model = scip.Model()

        y = [
            model.addVar(vtype="I", lb=0, obj=c, name=str(i))
            for i, c in enumerate(route_costs)
        ]

        node_to_route_coeffs = {j: [] for j in nodes}

        for i, coeffs in enumerate(route_coeffs):
            for j, a in coeffs.items():
                if j not in node_to_route_coeffs:
                    assert (
                        False
                    ), "Node {} used in the coefficient not in the set of nodes {}".format(
                        j,
                        nodes,
                    )

            node_to_route_coeffs[j].append((i, a))

        node_conss = {
            j: model.addCons(
                scip.quicksum(a * y[i] for i, a in coeffs) == 1,
                separate=False,
                modifiable=True,
            )
            for j, coeffs in node_to_route_coeffs.items()
        }

        if max_routes is not None:
            max_routes_cons = model.addCons(
                scip.quicksum(y) <= max_routes, separate=False, modifiable=True
            )
        else:
            max_routes_cons = None

        model.data = {
            "y": y,
            "node_conss": node_conss,
            "max_routes_cons": max_routes_cons,
        }

        return model

    @staticmethod
    def var_to_index(var):
        if var.name.startswith("t_"):
            return int(var.name[2:])
        else:
            return int(var.name)

    def optimize(self):
        self.model.optimize()
        status = self.model.getStatus()

        result = {
            "time": time.perf_counter() - self.started,
            "nodes": self.model.getNTotalNodes(),
        }

        if status == "infeasible":
            result["infeasible"] = True
        else:
            result["infeasible"] = False

            n_sols = self.model.getNSols()

            if n_sols == 0:
                result["solution_found"] = False
            else:
                result["solution_found"] = True
                result["cost"] = self.model.getObjVal()
                result["optimal"] = status == "optimal"
                result["routes"] = [
                    self.model.data["routes"][i]
                    for i, v in enumerate(self.model.data["y"])
                    if self.model.getVal(v) > 0.5
                ]

            result["best_bound"] = self.model.getDualbound()

        return result


class RoutePricer(scip.Pricer):
    def __init__(
        self,
    ):
        self.started = time.perf_counter()

        self.node_cons = None
        self.max_routes_cons = None

    def pricerinit(self):
        self.node_conss = {
            i: self.model.getTransformedCons(c)
            for i, c in self.model.data["node_conss"].items()
        }

        if self.model.data["max_routes_cons"] is not None:
            self.max_routes_cons = self.model.getTransformedCons(
                self.model.data["max_routes_cons"]
            )

    def add_column(self, name, coeffs, cost):
        v = self.model.addVar(vtype="I", lb=0, obj=cost, name=name, pricedVar=True)

        for j, a in coeffs.items():
            self.model.addConsCoeff(self.node_conss[j], v, a)

        if self.max_routes_cons is not None:
            self.model.addConsCoeff(self.max_routes_cons, v, 1)

        self.model.data["y"].append(v)

    @abstractmethod
    def pricerredcost_column(self, edges, node_costs, constant_cost, time_limit=None):
        pass

    @abstractmethod
    def pricerfarkas_column(self, edges, node_costs, constant_cost, time_limit=None):
        pass

    def time_remaining(self):
        """
        Get the time remaining in seconds
        """

        if self.model.data["has_time_limit"]:
            time_limit = self.model.getParam("limits/time")
            elapsed_time = self.model.getSolvingTime()

            return time_limit - elapsed_time
        else:
            return None

    def price(self, farkas):
        if self.model.data["verbosity"] >= 2:
            current_id = self.model.getCurrentNode().getNumber()
            print("At node {}, LP obj: {}".format(current_id, self.model.getLPObjVal()))

        edges = copy.deepcopy(self.model.data["edges"])

        for cons in self.model.data["conshdlr"].conss:
            if cons.isActive():
                edges.discard(cons.data.edge)

        time_limit = self.time_remaining()

        if time_limit is not None and time_limit <= 0.0:
            return scip.SCIP_RESULT.DIDNOTRUN, None

        if farkas:
            node_costs = {
                i: -self.model.getDualfarkasLinear(c)
                for i, c in self.node_conss.items()
            }

            if self.max_routes_cons is None:
                constant_cost = 0
            else:
                constant_cost = -self.model.getDualfarkasLinear(self.max_routes_cons)

            pricing_iterator = self.pricerfarkas_column(
                edges, node_costs, constant_cost, time_limit=time_limit
            )
        else:
            node_costs = {
                i: -self.model.getDualsolLinear(c) for i, c in self.node_conss.items()
            }

            if self.max_routes_cons is None:
                constant_cost = 0
            else:
                constant_cost = -self.model.getDualsolLinear(self.max_routes_cons)

            pricing_iterator = self.pricerredcost_column(
                edges, node_costs, constant_cost, time_limit=time_limit
            )

        key_to_route = {}
        route_to_coeffs_cost = {}
        min_redcost = None
        timed_out = False

        for route, coeffs, cost, redcost, stopped in pricing_iterator:
            if route is not None:
                key = tuple(sorted(coeffs.items()))

                if key in key_to_route:
                    best_route = key_to_route[key]
                    _, best_cost = route_to_coeffs_cost[best_route]

                    if best_cost <= cost:
                        continue
                    else:
                        del route_to_coeffs_cost[best_route]

                key_to_route[key] = route
                route_to_coeffs_cost[route] = (coeffs, cost)

                if min_redcost is None or (
                    redcost is not None and redcost < min_redcost
                ):
                    min_redcost = redcost

            timed_out |= stopped

        for route, (coeffs, cost) in route_to_coeffs_cost.items():
            index = len(self.model.data["routes"])
            self.model.data["routes"].append(route)
            self.add_column(str(index), coeffs, cost)

            for edge in zip(route[:-1], route[1:]):
                if edge not in self.model.data["edge_to_route_indices"]:
                    self.model.data["edge_to_route_indices"][edge] = []

                self.model.data["edge_to_route_indices"][edge].append(index)

        if self.model.data["verbosity"] >= 2:
            print("Priced {} columns".format(len(route_to_coeffs_cost)))

        status = scip.SCIP_RESULT.SUCCESS

        if timed_out:
            min_redcost = None
            if len(route_to_coeffs_cost) == 0:
                status = scip.SCIP_RESULT.DIDNOTRUN

        return status, min_redcost

    def pricerredcost(self):
        result, min_redcost = self.price(farkas=False)

        if min_redcost is not None:
            max_routes = (
                len(self.model.data["nodes"])
                if self.model.data["max_routes"] is None
                else self.model.data["max_routes"]
            )

            lowerbound = self.model.getLPObjVal() + max_routes * min_redcost

            if lowerbound > self.model.getCurrentNode().getLowerbound():
                return {"result": result, "lowerbound": lowerbound}

        return {"result": result}

    def pricerfarkas(self):
        result, _ = self.price(farkas=True)

        return {"result": result}
