from pytest import fixture

from mcstatus.forge_data import RawForgeData
from mcstatus.motd import Motd
from mcstatus.status_response import ForgeData, JavaStatusPlayer, JavaStatusPlayers, JavaStatusResponse, JavaStatusVersion
from tests.status_response import BaseStatusResponseTest


@BaseStatusResponseTest.construct
class TestJavaStatusResponse(BaseStatusResponseTest):
    RAW = {
        "players": {"max": 20, "online": 0},
        "version": {"name": "1.8-pre1", "protocol": 44},
        "description": "A Minecraft Server",
        "favicon": "data:image/png;base64,foo",
    }

    EXPECTED_VALUES = [
        ("players", JavaStatusPlayers(0, 20, None)),
        ("version", JavaStatusVersion("1.8-pre1", 44)),
        ("motd", Motd.parse("A Minecraft Server", bedrock=False)),
        ("latency", 0),
        ("icon", "data:image/png;base64,foo"),
        ("raw", RAW),
        ("forge_data", None),
    ]
    OPTIONAL_FIELDS = [("favicon", "icon")], {
        "players": {"max": 20, "online": 0},
        "version": {"name": "1.8-pre1", "protocol": 44},
        "description": "A Minecraft Server",
        "favicon": "data:image/png;base64,foo",
    }

    @fixture(scope="class")
    def build(self):
        return JavaStatusResponse.build(self.RAW)  # type: ignore # dict[str, Unknown] cannot be assigned to TypedDict


@BaseStatusResponseTest.construct
class TestJavaStatusPlayers(BaseStatusResponseTest):
    EXPECTED_VALUES = [
        ("max", 20),
        ("online", 0),
        (
            "sample",
            [
                JavaStatusPlayer("foo", "0b3717c4-f45d-47c8-b8e2-3d9ff6f93a89"),
                JavaStatusPlayer("bar", "61699b2e-d327-4a01-9f1e-0ea8c3f06bc6"),
                JavaStatusPlayer("baz", "40e8d003-8872-412d-b09a-4431a5afcbd4"),
            ],
        ),
    ]
    OPTIONAL_FIELDS = [("sample", "sample")], {
        "max": 20,
        "online": 0,
        "sample": [
            {"name": "foo", "id": "0b3717c4-f45d-47c8-b8e2-3d9ff6f93a89"},
            {"name": "bar", "id": "61699b2e-d327-4a01-9f1e-0ea8c3f06bc6"},
            {"name": "baz", "id": "40e8d003-8872-412d-b09a-4431a5afcbd4"},
        ],
    }

    @fixture(scope="class")
    def build(self):
        return JavaStatusPlayers.build(
            {
                "max": 20,
                "online": 0,
                "sample": [
                    {"name": "foo", "id": "0b3717c4-f45d-47c8-b8e2-3d9ff6f93a89"},
                    {"name": "bar", "id": "61699b2e-d327-4a01-9f1e-0ea8c3f06bc6"},
                    {"name": "baz", "id": "40e8d003-8872-412d-b09a-4431a5afcbd4"},
                ],
            }
        )

    def test_empty_sample_turns_into_empty_list(self):
        assert JavaStatusPlayers.build({"max": 20, "online": 0, "sample": []}).sample == []


@BaseStatusResponseTest.construct
class TestJavaStatusPlayer(BaseStatusResponseTest):
    EXPECTED_VALUES = [("name", "foo"), ("id", "0b3717c4-f45d-47c8-b8e2-3d9ff6f93a89")]

    @fixture(scope="class")
    def build(self):
        return JavaStatusPlayer.build({"name": "foo", "id": "0b3717c4-f45d-47c8-b8e2-3d9ff6f93a89"})

    def test_id_field_the_same_as_uuid(self):
        build = JavaStatusPlayer.build({"name": "foo", "id": "0b3717c4-f45d-47c8-b8e2-3d9ff6f93a89"})
        assert build.id is build.uuid

        build.id = unique = object()  # type: ignore[assignment]
        assert unique is build.uuid


@BaseStatusResponseTest.construct
class TestJavaStatusVersion(BaseStatusResponseTest):
    EXPECTED_VALUES = [("name", "1.8-pre1"), ("protocol", 44)]

    @fixture(scope="class")
    def build(self):
        return JavaStatusVersion.build({"name": "1.8-pre1", "protocol": 44})


@BaseStatusResponseTest.construct
class TestForgeData(BaseStatusResponseTest):
    EXPECTED_VALUES = [
        ("fml_network_version", 3),
        (
            "channels",
            [
                {
                    "res": "cyclopscore:channel_main",
                    "version": "1.0.0",
                    "required": True,
                },
                {
                    "res": "supermartijn642configlib:sync_configs",
                    "version": "1",
                    "required": False,
                },
                {
                    "res": "alexsmobs:main_channel",
                    "version": "1",
                    "required": False,
                },
                {
                    "res": "sophisticatedcore:channel",
                    "version": "1",
                    "required": False,
                },
                {
                    "res": "rftoolsbase:rftoolsbase",
                    "version": "1.0",
                    "required": True,
                },
                {
                    "res": "irongenerators:irongenerators",
                    "version": "1",
                    "required": False,
                },
                {
                    "res": "xaeroworldmap:main",
                    "version": "1.0",
                    "required": True,
                },
                {
                    "res": "cookingforblockheads:network",
                    "version": "1.0",
                    "required": False,
                },
                {"res": "xnet:xnet", "version": "1.0", "required": True},
                {
                    "res": "placebo:placebo",
                    "version": "1.0.0",
                    "required": True,
                },
                {
                    "res": "citadel:main_channel",
                    "version": "1",
                    "required": False,
                },
                {
                    "res": "sophisticatedbackpacks:channel",
                    "version": "1",
                    "required": False,
                },
                {
                    "res": "buildinggadgets:main",
                    "version": "4",
                    "required": False,
                },
                {
                    "res": "mekanismgenerators:mekanismgenerators",
                    "version": "10.2.5",
                    "required": False,
                },
                {
                    "res": "waila:networking",
                    "version": "1.0.0",
                    "required": True,
                },
                {
                    "res": "shetiphiancore:main_channel",
                    "version": "1.0.0",
                    "required": False,
                },
                {
                    "res": "dummmmmmy:dummychannel",
                    "version": "1",
                    "required": False,
                },
                {
                    "res": "supplementaries:network",
                    "version": "1",
                    "required": False,
                },
                {
                    "res": "refinedstorage:main_channel",
                    "version": "1",
                    "required": False,
                },
                {"res": "corpse:default", "version": "1.0.0", "required": True},
                {
                    "res": "ping:ping_channel",
                    "version": "PING1",
                    "required": True,
                },
                {
                    "res": "ironfurnaces:ironfurnaces_network",
                    "version": "1.0",
                    "required": True,
                },
                {"res": "botania:main", "version": "0", "required": False},
                {"res": "curios:main", "version": "1", "required": False},
                {"res": "patchouli:main", "version": "1", "required": False},
                {"res": "camera:default", "version": "1.0.0", "required": True},
                {
                    "res": "libnonymous:channel",
                    "version": "1.0",
                    "required": True,
                },
                {
                    "res": "elevatorid:main_channel",
                    "version": "1",
                    "required": False,
                },
                {"res": "worldedit:cui", "version": "1", "required": True},
                {"res": "worldedit:internal", "version": "1", "required": True},
                {"res": "cfm:network", "version": "1", "required": False},
                {
                    "res": "architectury:network",
                    "version": "1",
                    "required": True,
                },
                {"res": "trashcans:main", "version": "1", "required": False},
                {"res": "jei:channel", "version": "1.0.0", "required": True},
                {"res": "ae2:main", "version": "1", "required": True},
                {
                    "res": "mekanism:mekanism",
                    "version": "10.2.5",
                    "required": False,
                },
                {"res": "bdlib:multiblock", "version": "2", "required": False},
                {"res": "bdlib:misc", "version": "1", "required": False},
                {"res": "create:main", "version": "1", "required": False},
                {
                    "res": "waystones:network",
                    "version": "1.0",
                    "required": False,
                },
                {"res": "comforts:main", "version": "1", "required": False},
                {
                    "res": "naturescompass:naturescompass",
                    "version": "1.0",
                    "required": True,
                },
                {
                    "res": "storagenetwork:main_channel",
                    "version": "1",
                    "required": False,
                },
                {"res": "cofh_core:general", "version": "1", "required": True},
                {
                    "res": "mcjtylib:mcjtylib",
                    "version": "1.0",
                    "required": True,
                },
                {
                    "res": "mininggadgets:main_network_channel",
                    "version": "2",
                    "required": False,
                },
                {
                    "res": "crafttweaker:main",
                    "version": "1.0.0",
                    "required": False,
                },
                {"res": "akashictome:main", "version": "1", "required": False},
                {
                    "res": "forge:tier_sorting",
                    "version": "1.0",
                    "required": False,
                },
                {"res": "forge:split", "version": "1.1", "required": True},
                {
                    "res": "colossalchests:channel_main",
                    "version": "1.0.0",
                    "required": True,
                },
                {"res": "selene:network", "version": "1", "required": False},
                {
                    "res": "craftingtweaks:network",
                    "version": "1.0",
                    "required": False,
                },
                {
                    "res": "minecraft:unregister",
                    "version": "FML3",
                    "required": True,
                },
                {
                    "res": "minecraft:register",
                    "version": "FML3",
                    "required": True,
                },
                {"res": "titanium:network", "version": "1.0", "required": True},
                {
                    "res": "easy_villagers:default",
                    "version": "1.0.0",
                    "required": True,
                },
                {"res": "pipez:default", "version": "1.0.0", "required": True},
                {"res": "mantle:network", "version": "1", "required": False},
                {"res": "quark:main", "version": "1", "required": False},
                {
                    "res": "xaerominimap:main",
                    "version": "1.0",
                    "required": True,
                },
                {
                    "res": "fastbench:channel",
                    "version": "4.6.0",
                    "required": True,
                },
                {"res": "polymorph:main", "version": "1", "required": False},
                {
                    "res": "storagedrawers:main_channel",
                    "version": "1",
                    "required": False,
                },
                {
                    "res": "enercell:network",
                    "version": "0.0.0",
                    "required": False,
                },
                {"res": "appleskin:sync", "version": "1", "required": True},
                {
                    "res": "modularrouters:main_channel",
                    "version": "2",
                    "required": False,
                },
                {
                    "res": "the_vault:network",
                    "version": "0.26.0",
                    "required": False,
                },
                {
                    "res": "modernui:fluxnetworks",
                    "version": "707",
                    "required": False,
                },
            ],
        ),
        (
            "mods",
            [
                {"modid": "rsrequestify", "modmarker": "2.2.0"},
                {"modid": "cyclopscore", "modmarker": "1.15.1"},
                {"modid": "auudio", "modmarker": "1.0.3"},
                {"modid": "auxiliaryblocks", "modmarker": "1.18.2-0.0.14"},
                {"modid": "supermartijn642configlib", "modmarker": "1.1.6"},
                {"modid": "alexsmobs", "modmarker": "1.18.6"},
                {"modid": "architects_palette", "modmarker": "1.1.2"},
                {"modid": "cagerium", "modmarker": "1.18.2-1.1.0"},
                {"modid": "mcwwindows", "modmarker": "2.0.3"},
                {
                    "modid": "sophisticatedcore",
                    "modmarker": "1.18.2-0.5.32.179",
                },
                {"modid": "thermal", "modmarker": "1.6.3.28"},
                {"modid": "rftoolsbase", "modmarker": "1.18-3.0.9"},
                {"modid": "initialinventory", "modmarker": "6.0.8"},
                {"modid": "irongenerators", "modmarker": "2.0.1"},
                {"modid": "xaeroworldmap", "modmarker": "1.25.1"},
                {"modid": "cookingforblockheads", "modmarker": "12.0.2"},
                {
                    "modid": "controlling",
                    "modmarker": "<not required for client>",
                },
                {"modid": "xnet", "modmarker": "1.18-4.0.5"},
                {"modid": "placebo", "modmarker": "6.4.1"},
                {"modid": "citadel", "modmarker": "1.11.3"},
                {"modid": "powah", "modmarker": "3.0.1-beta"},
                {"modid": "bookshelf", "modmarker": "13.2.50"},
                {"modid": "lootbeams", "modmarker": "1.18.1"},
                {
                    "modid": "sophisticatedbackpacks",
                    "modmarker": "1.18.2-3.18.35.752",
                },
                {"modid": "twigs", "modmarker": "1.1.4-patch1+1.18.2"},
                {
                    "modid": "buildinggadgets",
                    "modmarker": "3.13.0-build.5+mc1.18.2}",
                },
                {"modid": "darkutils", "modmarker": "10.0.5"},
                {"modid": "mcwdoors", "modmarker": "1.0.6"},
                {"modid": "waddles", "modmarker": "1.18.2-0.8.19"},
                {"modid": "mekanismgenerators", "modmarker": "10.2.5"},
                {"modid": "balm", "modmarker": "3.2.0+0"},
                {"modid": "waila", "modmarker": "<not required for client>"},
                {"modid": "jeresources", "modmarker": "0.14.1.171"},
                {
                    "modid": "cloth_config",
                    "modmarker": "<not required for client>",
                },
                {"modid": "shetiphiancore", "modmarker": "3.10.10"},
                {"modid": "dummmmmmy", "modmarker": "1.18-1.5.2"},
                {"modid": "supplementaries", "modmarker": "1.18.2-1.5.13"},
                {"modid": "refinedstorage", "modmarker": "1.10.2"},
                {"modid": "konkrete", "modmarker": "1.3.3"},
                {"modid": "easy_piglins", "modmarker": "1.18.2-1.0.0"},
                {"modid": "corpse", "modmarker": "1.18.2-1.0.2"},
                {"modid": "packmenu", "modmarker": "<not required for client>"},
                {"modid": "mcwbridges", "modmarker": "2.0.3"},
                {"modid": "torchmaster", "modmarker": "18.1.0"},
                {"modid": "compressium", "modmarker": "1.4.2-build.9+mc1.18.2"},
                {"modid": "ping", "modmarker": "1.18-1.8.0"},
                {"modid": "ironfurnaces", "modmarker": "3.3.1"},
                {"modid": "mcwtrpdoors", "modmarker": "1.0.6"},
                {"modid": "mcwfences", "modmarker": "1.0.5"},
                {"modid": "supermartijn642corelib", "modmarker": "1.0.19"},
                {"modid": "simplylight", "modmarker": "1.18.2-1.4.2-build.31"},
                {"modid": "botania", "modmarker": "1.18.2-434"},
                {"modid": "highlighter", "modmarker": "ANY"},
                {"modid": "spark", "modmarker": "<not required for client>"},
                {"modid": "curios", "modmarker": "1.18.2-5.0.7.1"},
                {"modid": "patchouli", "modmarker": "1.18.2-71.1"},
                {"modid": "camera", "modmarker": "1.18.2-1.0.4"},
                {"modid": "blockcarpentry", "modmarker": "1.18-0.3.0"},
                {"modid": "thermal_foundation", "modmarker": "1.6.3.28"},
                {"modid": "thermal_expansion", "modmarker": "1.6.3.13"},
                {"modid": "libnonymous", "modmarker": "2.1.0"},
                {"modid": "elevatorid", "modmarker": "1.18.2-1.8.4"},
                {"modid": "runelic", "modmarker": "11.0.1"},
                {
                    "modid": "worldedit",
                    "modmarker": "<not required for client>",
                },
                {"modid": "cfm", "modmarker": "7.0.0-pre29"},
                {"modid": "architectury", "modmarker": "4.9.84"},
                {"modid": "weirdinggadget", "modmarker": "2.2.11"},
                {"modid": "mcwfurnitures", "modmarker": "3.0.0"},
                {"modid": "trashcans", "modmarker": "1.0.15"},
                {"modid": "mcwlights", "modmarker": "1.0.3"},
                {"modid": "cucumber", "modmarker": "5.1.2"},
                {"modid": "snad", "modmarker": "1.18.2-1.22.04.15a"},
                {"modid": "jei", "modmarker": "9.7.0.209"},
                {"modid": "ae2", "modmarker": "11.1.4"},
                {"modid": "mekanism", "modmarker": "10.2.5"},
                {"modid": "bdlib", "modmarker": "1.19.3.7"},
                {"modid": "create", "modmarker": "0.5.0.d"},
                {"modid": "waystones", "modmarker": "10.1.0"},
                {"modid": "clumps", "modmarker": "8.0.0+10"},
                {"modid": "shutupexperimentalsettings", "modmarker": "1.0.5"},
                {"modid": "comforts", "modmarker": "1.18.2-5.0.0.4"},
                {"modid": "naturescompass", "modmarker": "1.18.2-1.9.7-forge"},
                {"modid": "storagenetwork", "modmarker": "1.18.2-1.6.1"},
                {"modid": "framedcompactdrawers", "modmarker": "1.18-4.1.0"},
                {"modid": "decorative_blocks", "modmarker": "2.1.0"},
                {"modid": "botanypots", "modmarker": "8.0.12"},
                {"modid": "ftbbackups2", "modmarker": "1.0.17"},
                {"modid": "cofh_core", "modmarker": "1.6.4.21"},
                {"modid": "mcjtylib", "modmarker": "1.18-6.0.15"},
                {"modid": "ispawner", "modmarker": "1.0"},
                {"modid": "everycomp", "modmarker": "1.18.2-1.5.7"},
                {"modid": "jeitweaker", "modmarker": "3.0.0.8"},
                {"modid": "terralith", "modmarker": "0.0NONE"},
                {"modid": "mininggadgets", "modmarker": "1.11.0"},
                {"modid": "crafttweaker", "modmarker": "9.1.197"},
                {"modid": "akashictome", "modmarker": "1.5-20"},
                {"modid": "forge", "modmarker": "ANY"},
                {"modid": "colossalchests", "modmarker": "1.8.3"},
                {"modid": "selene", "modmarker": "1.18.2-1.17.9"},
                {"modid": "drippyloadingscreen", "modmarker": "1.6.4"},
                {
                    "modid": "craftingtweaks",
                    "modmarker": "<not required for client>",
                },
                {"modid": "minecraft", "modmarker": "1.18.2"},
                {"modid": "terrablender", "modmarker": "1.18.2-1.1.0.102"},
                {
                    "modid": "sophisticatedbackpacksvh",
                    "modmarker": "1.18.2-1.0.4.12",
                },
                {"modid": "mousetweaks", "modmarker": "ANY"},
                {"modid": "titanium", "modmarker": "3.5.6"},
                {"modid": "jade", "modmarker": "<not required for client>"},
                {"modid": "createtweaker", "modmarker": "2.0.0.17"},
                {"modid": "easy_villagers", "modmarker": "1.18.2-1.0.10"},
                {"modid": "pipez", "modmarker": "1.18.2-1.1.5"},
                {"modid": "iceberg", "modmarker": "ANY"},
                {"modid": "flywheel", "modmarker": "<not required for client>"},
                {"modid": "mantle", "modmarker": "1.9.27"},
                {"modid": "ecologics", "modmarker": "1.7.3"},
                {"modid": "quark", "modmarker": "3.2-358"},
                {"modid": "xaerominimap", "modmarker": "22.11.1"},
                {"modid": "pigpen", "modmarker": "8.0.1"},
                {"modid": "fastbench", "modmarker": "6.0.2"},
                {"modid": "polymorph", "modmarker": "1.18.2-0.44"},
                {"modid": "autoreglib", "modmarker": "1.7-53"},
                {"modid": "storagedrawers", "modmarker": "10.2.1"},
                {"modid": "fluxnetworks", "modmarker": "7.0.7.8"},
                {"modid": "neoncraft2", "modmarker": "2.2"},
                {"modid": "enercell", "modmarker": "0.0NONE"},
                {"modid": "appleskin", "modmarker": "2.4.0+mc1.18"},
                {
                    "modid": "ferritecore",
                    "modmarker": "<not required for client>",
                },
                {"modid": "modularrouters", "modmarker": "9.1.1-93"},
                {"modid": "refinedstorageaddons", "modmarker": "0.8.2"},
                {"modid": "openloader", "modmarker": "12.0.1"},
                {"modid": "the_vault", "modmarker": "1.18.2-2.0.10.869"},
            ],
        ),
        ("truncated", False),
    ]

    @fixture(scope="class")
    def build(self):
        return ForgeData.build(
            RawForgeData(
                {
                    "channels": [],
                    "d": bytes.fromhex(
                        "e0ba8b0000c484e4a0b0e18e9be19997e2baaee1b399e392bae7a5a6e6908ae4a2b8c5b1e380a3e2b1a1e1a39ee39eb6e78db0e5bb86e19789e0a0b3e18ba3e49aa6e0b18be38686e685a8e5b39ce38695e6abbbe19896e2b78de0b181e1a097e380ae02d098e2aeabe19987e2b7ade0b181e1a097e38caee1b880e59684e4af83e19b86e4b0ade1b99ce398b1e68dafe69b96e490b5e0a5b1e68e83e29985e0b08be1a097e384aed1a8e4b1a0ceabe29997e2b6aee1b298e392bae6b9aae6a1ace0b388e78dbbe199a6e0b3ade1a99bcab1e2b8b1e5b1a2e38398e4ae98e39ba7e6aface1af98e38cb7e69da9cba6c384e4a090e49890e0b2ade5b39ee39eb6e78da2e6888ce492b8e78781e48da2e2b6a1e1a998e2beb7e6a1a3e5b382e196b9e0ada3cc90e48080e1a184e386b9e6a5a8e4aba8e5868de7ae9be19c85e2b68ce1b499e38abae38485e6899ce4a2b8e48081e198b0e2b3ace5b299e3aab4e0b1ade5b1a2e68384e185b1e18b93e29786e0ae8c18e6b48ae6bb86e2979de28db3e79bb6e2b9aee0b281e1a097e38caee28884e3b78ce48e83e39a96e2ba8ee5a39ae3a8b0e691a5e5bb86e19789e0a28be18ba3e49c86e4b28be1a096e394aee6999ce3a388e3a689e78e93e0b1a0e1a19ae39cb7e6b1a5e6888200e280b8e59a87e2b98ce1a19bd0b6e2b8b1e5b1ace3a38ce48691e380a3e4b981e5b499e39eb7e78dace48b84e1978de0a193e18ba3e29c86e0b38be1a097e3a4aee69096e58699e7adbbe39b86e2b18ee5b398c6b2e2b8b1c9a0e48080e78d88e49a96e2b4aee5ac98e39cb4e695b6e6a39ce4a6bde2af8be68da0e49885e0b88bdc81e789a9e5b39ee1969de2adb3e19ca6e6ba8ce5b29bcab9e2b8b2e5b1a0e3a384e18d88e69bb7e2b3ade5ae99e3a4b2e791a1e6939ed78dc688e580a0e2bc81e1a598e39eb9e6bdb7e5a3a4e39691cc8be181a7e49786e0b58ce1a297e6b484e58b82e0b6b9e78688e18c8240e5a385e39eb7e6a5abe4bb9ce3b699e18e93e79b86e6b1ade5a89ae382b2e78da4e6888ce3a388e78681e78ca2e2b780e5b499e39ebbe6adb2e68886e482b8e0a081e382b0e4b7ace1b49be39eb9e6b1ace5b392e0a69de480a0e59ba7e4ba8ce0b182e1a297e2b4b8e5b1a8e3a380e286a9e69e80e0b2ade4839de19c98c4b0e0b884e38780e1ac8be29996e2b7ace0b681e1a897e384aee6808ed6b1e2ac9be798a6e282ade0ae8ce19c98c4b0e0b884e2968ce0aea3e59986e4b68ce0b181e1a297e2b8b1e1a1a6d6b4e78d8be397b6e2b48ce1ae98e38ab7c5ac62e19080e7ae80e19db6e4b48ce0b382e1a097e384aee4919ae58695cc8be28290e6b7ace5ab9be390b9e6b1a5e0bb8ce4b384e185b1e58ba3d886c980e39eb6e791afe4ab84e39685e38e9be68c90d8a5e4ae8ec498e78c96e6839ee296a1e28e9be39a97e0b0ace1a59de384b2e68da1e68396e0b685e1ad9be184a7e29786e0b88ce1a497e38cade6899ce3a3a0e2a699e78ba3e49aa6e4878ce390b1e6b9a1e4ab9cd6b1c688e58080e6ba80e5a99de3a6b3e38493e6899ce582b8c5a9e49897e0b1aee4b19ae1a295e384aee5b1b0e0a388e181b8e19d96e0b68de1a999e38eb7e685a7e4bb88e58695e48e9be68cb1e698a5e0ae8ce19a98e795a2e5a392e3a691e5a6a9e39b92e498ace0b18be19c9ce7b4b2e5a888e29685e0adb3cd80e28080e5a482e3a4b0e795abe58ba8e4b6b1e0a0b3e68c83e49885e0b58bd080e68dade4a3aee3b6bde1ae93e18197d786e0ae8c1be79c87e4a382e38691e1acabe18397e29786e0b88ce1a497e380ade7819ce492b8e18789e584a0e6b2ade1a19ae392b7e6b5b3e4ab8ee196b9e0ae93e79d86e6b98de4869ce1a098e388aee6a99ce39188e5acabe69896e6b4ade5ad9ce38ab3e695aee48ba4e3b791e1ae93e181a7e49886e0b28be1aa9700e49088e38685e3adabe68cb0e49985e4b08be1a095d483e48baee386a5e58c8be59ba0e6ba8ce1af9de396b9e6b9a9e0ab8ee3a384e78681e18c82e68080e5aa82e3a4b2e78da5e6ab9ee0b789e1acabc2a7e29786e0b48ce1a297e384aee689aee38084e68c98e49bb6e6b48ee5a397e39cb7e6a5a6d38ee4b0b8e2ad83e19d86e0b88de5a99ae39cb0e6bda3e4aba4e4b09de0a5b1e68c83d8a5e48c8ce382b6e6b9a9e49abed6a1e78db3e49996e282ade0ae8ce19c9830e18884e59690e6adabe59b96e2b6ade1b99be1a285e384aee5a9b0e3a384e786a9e48ca2e2b281e5ad9de3b2b6e6a1a3e5b382e196b9e0ada3cc90e68180e5b383e3a0bae6b1b0e5ab8ae3a695e0aea3e19ca6e6b2ade48d9ce19c98e3a0b1e6919ce492b4e2a5b1e18ba3e699a6e5ae81e3a8b2e6bdb7e59ba4e49085e18081e283a0e4b2aee1a999e38ab7e78da4e5bba8d789e2acbbe181a6e29786e0b08ce1a497e6b48ce58b82e7b6b9e48c9ae69896e2b78de5ac99e1a28000e59890e3a6bde18d9be49997e2b2aee0b181e1a697e38caee1a080d694e4ae9bd7b7e6b4aee5ac99e39cb4e0b1b3e5b1a2e68384e185b1e18b93d786e0ae8cc498e68c86e6939ee4b781e68cabe68c90d8a5e0ae8ee19a99e2b8b1e5b1a0e1b388e2aca0e199a6e0baace5b49be1a282e380aee6819cd08440e39897e2b5ace1a59be3aab7e0a880e49b9ae0a79de4ae93e79986e6b2acc59ce19c99e2b8b066e580ace18dbbd8b7e2b6ade1b398e38abad9b2e781a2e492b8c5b1e38083e6b1a1e1ad9be3a4b8e78da5e58ba6e39795e0a2b3e48ba3e49786e0ad8ce3aab1e6b1a9e5b388e2b3a4e1ada9e68c96d8a5e0ae8ec499e78084e5b392e2a69de78688cc92e296a7e0ae8ce19c9ce0b0b0e58ba0e1b6b9e1abbbe19a86e4b78ce1a59bcab6e4a590e0ba9cd385e68090e29a90e4b7aee5a69be3a4bae685aee4ab86e1978de78698e68cb2d8a5e1a985e39eb9e699aee693aad6b9e2ac9be79cb6e2b78be5b499e39ebbe6adb2e68886e482b809e582b0e6b1ade1b49de3a0b9e6bda4e6939ee1978de78688e68c82db85e48980e386b6e699b7e5b38ae1968de2ae9be68c90e49885e0b58be0ac80e795b3e4aba0e39789e18c8be19d87e4b58de0b69be1a49ae6bda3e4aba4e296b1e38c93e68c90e49885e4b18b1ce78c8be5ab92e38781e68f8be79a96e0b48ce4959de19c98e3a0b1e6919ce492b4e285b1e28ba3e496a6e5b598e398b4e2b9a4e689a6e1b088e7ac90e19d86e2b78ce1a19ae1a285e384aee5b1b0e39388e1a6a1e48d83e2b6a0e1a998c2b730e19880e296a0e48cbbe19b86e0b3ade5b49ae3a4b2e48483e38a9ce19085ce98e29897e4b5aee48680e3aab1e6a5b2e69b9ee490b9e0a5b1e68e83e29985e0b58be1a097e39caee6899ce39090e4ac8be19ba6d8a0e48280e3a084e791a1e58386e596bde4ada3e182b6e29786e0b88ce1a497e39cade5b1a2e18384e0ada8e69a96e280ad0ccc81e685a3e4ab9ad789e0a1a3e18ba3e49c86e4b28be1a296e380aee6a19ce1809ce38cabe59896e0b68ee4859de19c98e2b8b0c9a0e3a080e68c90e39bb6e6b5ace1a198e3a0b9e6b9a5e693a8e2a7a5e78688cc92d6a7e4ae8ce19c9930e6a0a4e196a1e6ae93e49896e4afade5af99e39cbae685a4e58ba8e3a6bde0a183e68ba3e69786e0ae8ce1b099e18480e583a8e4a695e0adabe79b86e0b2abe5b09ee39cb0e6a5b3e5b39ee490a1e385b1e38ba3e29786e0b38cd681e6a5ace5b384e3a6bde6af8be59bb6e2b9aee0b281e1a297e380aee4988ed6a1e78db3e49996e281ade0ae8cc298e0a882e5a38ae5a695e28c8be29bb7e0b4aee48c99e19c98e3a0b1e6919ce492b4e485b1e48ba3e28686e5a19be39cb4e68d9fe48b90e3a6b9e68cabe1809606c780e3aab9e695aee58b98e1a68de0a688cba3e29786e4858ce3ae84e789afe4a398e18695e28d8be380b7e2baace4819ac298e6a488e6a39ce4a695e0adb3e19b86e298a0e48280e38681e6b5a6e6b896e482b8c5b1cb93e2b98ee4b299ce9ce695aee6bba8e4a6bde0ad9bcc9040e1a183e386b9e6a5a8e4aba8e5868de18eabe69e97e49a80e0b98be1b097dcb4e4ab9ce5b791e18dbbe19ab7e298a000e3ae87e6a5a5e4a3a4e3a6a5e3acbbe49896e2b3ace1b499e1a483e388aee6899cc384e6a1a8e798b6e2b38ee1b29de392b7e795b4e4aba4e1978de78698e68c82e49885c980e3a4bae78da1e49b90e3a685e38e9be68c90e49885e4b18bc89ae685ade5b392e4908501e58290e6b1ade5ac9de38eb4e791a8e0aba6e3a384e78681ccb2e68480e5b598e3aab1e689ade6938ae59095e0a5b1e28ba306e1b381e382b7e189a4e5b1a2e68384e185b1e18b93e49786e0b28ce1a097e2b8b4e6a9a2e0a684e58098e19996e284ade4ae8ee19c9be2b8b0e681a4e1b3a4e48c98e69896e2b78de5ac99e1a282e380aee6819ce0a084e0a098e29996e28386e0b18ce1a297e390aee5a888e29685e0adb3e18c9040e5ad82e396b2e6b9a1e69b92e1a6b5c688e28ba3e29786e4888de38ab6e685abe58b9ce3978de0a0b3e68c83e49985e0b58bc880e68885e5a388e0a6a5e0a183e18ba3e49ca6e0b38be1ae97e6b48ae5a3aae29791e68c93e39bb6e2b5ace0b280c880e6a5ade49ba6e49085e18081e381a0e2b98ce1a199e38abae38087e6a99ce482b8e285b1e58186e2b0ade5ae9ae1a280c880e6b892e69685e28e9be69bb7e6b2ade4869ce1a098e384aee6819ce3a09ce28cabe79db7e6b98de4839ae19c9830e0b080e3868ce6aeabe39c86c48ee0ae8ee19c98e2acb0e681a2e6a080e48e98e49d96e0baaee1a59ce3a0bce789a5e5ab92e3a695e0aea3e39b86e0b2aee5b49de39cb4e78da7e6888ae482b8e2a5b123e6b1a1e1ad9be39eb3e791b2e1b3a6e3a384e48689e28ba3e296a6e0ae8de19c98e2b8b0e0a1a8d6b4e78d8be18096e48086ce80e382b7e795b4e4aba4e0b78de6adbbe19c86e6b9ace4929ce19c98e3a0b1e6919ce492b4e4a5b1e78ba3e496a6e1af99e38eb9e0b9a5e48b9ce59791e2ae93e39cb6e2b7ace5b09be3a6b0cdb3e5b1a2d380e78090e49cb0e4b7aee5a19ce38ab3e695aee6bba8e4a6bde68d9be68c90d8a5e0ae8ee19a99e2b8b1e5b1ace38384e0ada8e69a96e6afade5a898e39cb0e695aecb98c384e28080e299a1e2b0aee1a59be386b2e6b5afe48ba0e5868de18ca3e79897e4b2aee1b39ce1a285e384aee5a9b0e3a390e78689cc82c8a0e5a599e39eb1e685b2e58ba8e19799e18bbbe79b86e6b1ade5b39ae1a482e384aee6819ce2a080e7ac90e19d86e2b78ce5b09ee3a8b7d9b3e5b1b0e3a380e18689e38083e0b381e1a29de382b1e6ada3e683aae4a78de0a0b1cba3e29786e0b78cd281e6bda3e5838ce0b5bde18dbbd997e498a1e0b68be1a897e388aee0b9a2e1969ce2adb3e19ca6e2b68ce4b180c480e6b488e59386e69791e4ada3e398a6e498a1e0b18be19a9ce2b8b6e5b1a0e59384e6a181e298b6e2ba8de5ac9ee384b4e38483e6819c04e4a180dcb6e6b0aee5ae9de3a4b2e38483e6819ce29080e38ca8e29997e6bcaee5af98e3a0b6e3848ce6899ce3a3a0e6a691e68c92e49aa5e0b78bd480e695aae6a392e1979de5ac8be29996e683aee0ae8ce19c98e2b8b070e580a4e18cabe19ca7e2b68ce1b49aceb4e2b8b0e1b1a0e3a4bde188aae58390e4b4ade1a99be38eb7e685a7e4bb88e58695e38e9be68c90e298a5e0ae8ce0a898e685ade5b392e3a5bde28cabe79db7e6b98de59f9ae390b1e6b9a1e4ab9cd6b1c690e480a0e4b1a1e1a19ce3a8b3e79db4e48b8ae196ade3ae93e68e90e498a5e4b18be1ae9ce6b484e58b82e196b9e78688e68c82d885e48280e38285e685abe583a6e0b6a5e7aea3e59b96e2838ce4ae8ce19a9ae380b2e5a888e29685e0adb3cc90e28280e5a681e3a4b7e695a7c886e694b9e281a2e59a97e6b98ce5b397e3a4b7e6a5b4e4bb9ce4908dc5b1e58083e0b9a0e5ac9ce3a8b4e38483e6899ce0a084e1a1b0e49bb6e6b7ade5b39ce398b0e6a1a3e69b8ae4b791e0a0abcba3e69787e48c8ce390b1e6b9a1e4ab9ce7b6b1e0adaae69a96e282ade0ae8ce19c98c4b0e0b084e1978ce2ada3e59ba6e286ace4ae8ce1b098e388aee6899ae492b8e786b9e78e92e2b780e5b499e39ebbe6adb2e6888200e28298e19ca6e0b88de1b99ce39eb6e691a1e5b392e4b69de18c9be59997e2b78ce0b181e1ac97e390aee1b086e4a68ce38c8be19d86e6b78de5b499e38abbe6ada1e0bba6e196b8e3aea3e29bb7e6b5aee0b180e1a097d080e5a892e3a6a5e1acabe19ca6e0b38ce4869de19c98e3a0b1e6919ce590a8e18db3e79997e6b4ace5b49ce3a4b2e49884e1a29ad38de18180e79997e6b4ace5b49ce3a4b2e49884e1a29ad38de68080e59d80e4b98ce1a19ce398b1e6b9a5e4ab88e48789e78688cc92e49787e4ad8ce19c98e2b8b1e5b1a0e48384c691e38680e0b7aee5a89ce3a6b4e6a5b4e48b86e19791e18ca3e39896e0b5ace5a19ce396b1e799b3e1bb90e3a384e48689e28ba3e296a6e0ae8ce19c98e2b8b4e691a2e2b080e7ada8e39d96e0b2aee5b79de382b2e78dabc886e694b9e48092e19d80e2ba8de5ae98e3aab4d5ade5b1a6e3a394e3a6b1e59ba0e6ba8ce1af9de396b9e38483e6819cd084e580a0e49896e0b2ace48d80e3a4b1e685a5e4aba8e5b791e0acabe59ab6e0b98ce0b282e1a097e380aee6899ce0a39ce2a1b0e39896e6bcaee5b697e398b4e685ace4ab8ee4b789e0a1abe18ba3e49c86e4b28be1a296e380aee6899ce1b380e2aca0e199a6e0baace5b49be1a282e380aee6819ce0a08428da97e4b2aee48c9ee19c98e3a0b1e6919ce492b4e0a5b1e58ba3c3a6e1a599e382b3e6b1b5e0aba8e3a384e78681e18c82e68080e5a981e38ab1e695a2e4bba4d08de4a9b215e0b381e5b99be390bbe695a5d398e39098e78c8be49d86e4b2ade0b181e1b297e388aee0b9aee196b8e3aea3e29bb7e2b5aee0b18000e69489e5bb86e3b6b1e4acbbe398b6e282aee4ae8ce19c9bc8b3e6888ad795e5ae93e381b6e49786e4ad8ce1aa99d0b8e48b9ae3a6a5e0a08be28083c680e5a19ee3a4b2e6b5afe5b392e396a5cc8be281b7e49986e4b18be19c98d0b1e48b9ae3a6a5e0a09bcba326c680e392b8e781a7e5b38ae68095c5b1e18ba3e28186e5a682e3a6b0e689b4e5b38ae2868de380abcba3e49786e4878ce390b1e6b9a1e4ab9ce196b1e786a0e68da2e29885e48280e3a084e6b1afe5abb2e4a6bde48e83e182b6e29786e0b88ce1a497e380ade6a19ce18390e0ada8e69a96e280ad0cd480e795a1e5bba8e19789e68cbbe29a96e2838ce4ae8ce19a9be38cb5e1b084e5878ce18dbbe79897e0b2ace5b299e3aeb0e789a5e0b3a6e48384e185b1e18ba3e28686e5a19be39cb4e68d9fe48b90e3a6b9e68cabe1809606cc80e398b3e7a1b5e4ab9ce5b791e18dbbe39ab7e683aee0ae8de19c98e2b8b770e3a0a8e7acabe39ba6e2b98ce1a698e1a4bae38883e6919ce28088e78ca8e29996e2b1aee1ac99ceb6e2b8b0e1b1a0e3a4bde3a8aae59ba0e6ba8ce1af9de396b9e38085e6819ce482b8e18081e18290e0b88ce5ac9ce3a6b2e6a5abe1a39ce3a388e786a1e38c82e6b6a5e0b198e1a297d0b8e78ba6e0b6b9e0a08be18093e485a0e1a599e3a4b9e791a9e49b8ae4a6bde18cabe583a0e0b7ade1b599e382b6e789b2e6ab9ee19791e1ae93e18287e29787e4ae8ce19a98e38cb9e5a898e29685e7adb3d8b5e4b0ade5ae9be398b2e3888100e4a190e38cabe69a96e0b2ade1b399e39ebae685b2e4ab8ee18685e7aca3e39ba6c2aee0ae8ce19c9c32e5b894e19781e68db3e19bb6e2b28ce1b299e1a283e2b8b2e5b1a0e0a384e28188e59a87e4aface5a19de398bae185b4e5b1a2e68384e185b1e28b93d786e4ae8ce1a098e3a0aee789ace3a09ce28cabe79db7e6b98dc69ae19c98e398b2e6819cd080e6a2a8e49bb6e4b2ace5ae9ce392bae698bae6ab98e3a7a1e28cabe79db7e6b98de5b39ae1ae81e39cb000"
                    ).decode("utf-8"),
                    "fmlNetworkVersion": 3,
                    "mods": [],
                    "truncated": True,
                }
            )
        )
