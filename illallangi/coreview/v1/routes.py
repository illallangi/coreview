from flask import Blueprint, current_app
from flask_restful import Resource, Api, reqparse
from .snmp import get_system, get_interfaces
from json import dumps, loads, JSONDecodeError

interface_status = {
    "propVirtual": {
        "down": {
            "down": {
                1000: "Hidden",  # Shutdown VLAN Port
            },
        },
        "up": {
            "up": {
                1000: "Hidden",  # VLAN Ports
                0: "Hidden",  # Stack Ports
            },
        },
    },
    "other": {
        "up": {
            "up": {
                10000: "Hidden",  # Null Ports
            },
        },
    },
    "ethernet-csmacd": {
        "up": {
            "up": {
                10000: "10 Gig",
                1000: "Gigabit",
                100: "100 Meg",
                10: "10 Meg",
                0: "0",
            },
            "down": {k: "Down" for k in [10000, 1000, 100, 10]},
        },
        "down": {
            "down": {k: "Shutdown" for k in [10000, 1000, 100, 10]},
        },
    },
}

interface_class = {
    "Hidden": "light",
    "Virtual": None,
    "10 Gig": None,
    "Gigabit": None,
    "Down": "warning",
    "100 Meg": "danger",
    "10 Meg": "danger",
    "0": "danger",
    "Shutdown": "light",
}

blueprint = Blueprint("api", __name__, url_prefix="/api/v1")
api = Api(blueprint)


def tryloads(json):
    try:
        return loads(json)
    except JSONDecodeError:
        return {"json": json}


systemParser = reqparse.RequestParser()
systemParser.add_argument(
    "Cf-Access-Authenticated-User-Email", type=str, required=False, location="headers"
)


class SystemItem(Resource):
    def get(self):
        args = systemParser.parse_args()
        if args["Cf-Access-Authenticated-User-Email"] is None:
            return {"message": "ERROR: Unauthorized"}, 401
        data = get_system(
            current_app.config["SNMP_HOSTNAME"], current_app.config["SNMP_COMMUNITY"]
        )
        return {"message": "success", "data": data, "hash": hash(dumps(data))}


interfaceParser = reqparse.RequestParser()
interfaceParser.add_argument(
    "Cf-Access-Authenticated-User-Email", type=str, required=False, location="headers"
)
interfaceParser.add_argument(
    "sort", type=str, required=False, location="args", default="interface"
)


class InterfaceItems(Resource):
    def get(self):
        args = interfaceParser.parse_args()
        if args["Cf-Access-Authenticated-User-Email"] is None:
            return {"message": "ERROR: Unauthorized"}, 401
        if args["sort"] not in ["interface", "run"]:
            return {"message": "ERROR: Invalid Sort"}, 400

        data = [
            {
                k: v
                for k, v in {
                    **tryloads(interface.get("ifAlias", "{}")),
                    "interface": interface["ifDescr"],
                    "status": interface_status[interface["ifType"]][
                        interface["ifAdminStatus"]
                    ][interface["ifOperStatus"]][interface["ifHighSpeed"]],
                    "class": interface_class[
                        interface_status[interface["ifType"]][
                            interface["ifAdminStatus"]
                        ][interface["ifOperStatus"]][interface["ifHighSpeed"]]
                    ],
                }.items()
                if v is not None and v != ""
            }
            for interface in get_interfaces(
                current_app.config["SNMP_HOSTNAME"],
                current_app.config["SNMP_COMMUNITY"],
            )
            # if interface['ifType'] == 'ethernet-csmacd' # and interface['ifAdminStatus'] == 'up'
        ]
        # if args['sort'] == 'interface':
        #     data.sort(key=lambda x: x['interface'])
        if args["sort"] == "run":
            data.sort(key=lambda x: x.get("run", 0))

        return {
            "message": "success",
            "count": len(data),
            "data": data,
            "hash": hash(dumps(data)),
        }


whoAmIParser = reqparse.RequestParser()
whoAmIParser.add_argument(
    "Cf-Access-Authenticated-User-Email", type=str, required=False, location="headers"
)


class WhoAmI(Resource):
    def get(self):
        args = whoAmIParser.parse_args()
        if args["Cf-Access-Authenticated-User-Email"] is None:
            return {"message": "ERROR: Unauthorized"}, 401
        data = {
            "email": args["Cf-Access-Authenticated-User-Email"],
        }
        return {
            "message": "success",
            "data": data,
            "hash": hash(dumps(data)),
        }


api.add_resource(SystemItem, "/system")
api.add_resource(InterfaceItems, "/interfaces")
api.add_resource(WhoAmI, "/whoami")
