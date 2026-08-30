import asyncio

from pysnmp.hlapi.v3arch.asyncio import (
    SnmpEngine,
    CommunityData,
    UdpTransportTarget,
    ContextData,
    ObjectType,
    ObjectIdentity,
    get_cmd
)


# Ubuntu Server IP
SNMP_SERVER = "192.168.1.51"

# SNMP community configured in Ubuntu
COMMUNITY = "labmonitor"


async def test_snmp():

    engine = SnmpEngine()

    try:

        error_indication, error_status, error_index, var_binds = (
            await get_cmd(

                engine,

                CommunityData(
                    COMMUNITY,
                    mpModel=1
                ),

                await UdpTransportTarget.create(
                    (SNMP_SERVER, 161),
                    timeout=3,
                    retries=1
                ),

                ContextData(),

                # System Description
                ObjectType(
                    ObjectIdentity(
                        "1.3.6.1.2.1.1.1.0"
                    )
                ),

                # System Uptime
                ObjectType(
                    ObjectIdentity(
                        "1.3.6.1.2.1.1.3.0"
                    )
                ),

                # System Name
                ObjectType(
                    ObjectIdentity(
                        "1.3.6.1.2.1.1.5.0"
                    )
                ),

                # System Location
                ObjectType(
                    ObjectIdentity(
                        "1.3.6.1.2.1.1.6.0"
                    )
                )
            )
        )


        if error_indication:

            print(
                "❌ SNMP ERROR:",
                error_indication
            )

            return


        if error_status:

            print(
                "❌ SNMP RESPONSE ERROR:",
                error_status.prettyPrint()
            )

            return


        print(
            "\n========== SNMP SERVER DATA =========="
        )


        labels = [
            "System Description",
            "System Uptime",
            "System Name",
            "System Location"
        ]


        for label, item in zip(
            labels,
            var_binds
        ):

            print(
                f"{label}: "
                f"{item[1].prettyPrint()}"
            )


        print(
            "======================================\n"
        )


    finally:

        engine.close_dispatcher()


asyncio.run(
    test_snmp()
)