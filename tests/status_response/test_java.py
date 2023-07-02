from pytest import fixture

from mcstatus.motd import Motd
from mcstatus.status_response import JavaForgeData, JavaStatusPlayer, JavaStatusPlayers, JavaStatusResponse, JavaStatusVersion
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
                    {
                        "name": "foo",
                        "id": "0b3717c4-f45d-47c8-b8e2-3d9ff6f93a89",
                    },
                    {
                        "name": "bar",
                        "id": "61699b2e-d327-4a01-9f1e-0ea8c3f06bc6",
                    },
                    {
                        "name": "baz",
                        "id": "40e8d003-8872-412d-b09a-4431a5afcbd4",
                    },
                ],
            }
        )

    def test_empty_sample_turns_into_empty_list(self):
        assert JavaStatusPlayers.build({"max": 20, "online": 0, "sample": []}).sample == []


@BaseStatusResponseTest.construct
class TestJavaStatusPlayer(BaseStatusResponseTest):
    EXPECTED_VALUES = [
        ("name", "foo"),
        ("id", "0b3717c4-f45d-47c8-b8e2-3d9ff6f93a89"),
    ]

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
class TestJavaStatusVersion(BaseStatusResponseTest):
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
        return JavaForgeData.build(
            {
                "channels": [],
                "d": "\u0e8b\x00\x00Ą䠰\u139bᙗ⺮᳙㒺祦搊䢸ű〣ⱡᣞ㞶獰廆ᗉ࠳ዣ䚦ోㆆ慨峜㆕櫻ᘖⷍు᠗〮\x02И⮫ᙇⷭు᠗㌮Ḁ善䯃ᛆ䰭Ṝ㘱捯曖䐵ॱ掃♅ఋ᠗ㄮѨ䱠Ϋ♗ⶮᲘ㒺湪桬ೈ獻ᙦ೭ᩛʱ⸱屢ヘ䮘㛧毬ᯘ㌷杩˦Ä䠐䘐ಭ峞㞶獢戌䒸燁䍢ⶡᩘ⾷档峂ᖹୣ̐䀀ᡄㆹ楨䫨再箛ᜅⶌᴙ㊺ㄅ扜䢸䀁ᘰⳬ岙㪴౭屢惄ᅱዓ◆\u0b8c\x18洊滆◝⍳盶\u2e6eಁ᠗㌮∄㷌䎃㚖⺎壚㨰摥廆ᗉࢋዣ䜆䲋᠖㔮晜㣈㦉玓ౠᡚ㜷汥戂\x00‸嚇⹌ᡛж⸱屬㣌䆑〣乁崙㞷獬䋄ᗍࡓዣ✆ೋ᠗㤮搖写筻㛆ⱎ峘Ʋ⸱ɠ䀀獈䚖\u2d2e嬘㜴敶棜䦽⯋捠䘅ซ܁物峞ᖝ⭳ᜦ溌岛ʹ⸲屠㣄ፈ曷Ⳮ宙㤲瑡擞\u05cdƈ倠⼁ᥘ㞹潷壤㖑̋ၧ䗆ൌᢗ洄勂ඹ熈ጂ@壅㞷楫仜㶙᎓盆汭娚ゲ獤戌㣈熁猢ⷀ崙㞻歲戆䂸ࠁグ䷬ᴛ㞹汬峒ঝ䀠囧二ూᢗⴸ屨㣀↩枀ಭ䃝\u1718İค㇀ᬋ♖ⷬඁᨗㄮ怎ֱ⬛瘦₭\u0b8c\u1718İค▌ண噆䶌ుᢗ⸱ᡦִ獋㗶ⴌᮘ㊷Ŭb᐀简\u1776䴌ೂ᠗ㄮ䑚冕̋ₐ淬嫛㐹汥໌䳄ᅱ勣؆ɀ㞶瑯䫄㖅㎛挐إ䮎Ę猖惞□⎛㚗బᥝㄲ捡惖අ᭛ᄧ◆ฌᤗ㌭扜㣠⦙狣䚦䇌㐱湡䫜ֱƈ倀満婝㦳ㄓ扜傸ũ䘗౮䱚ᢕㄮ屰ࣈၸ\u1756ඍᩙ㎷慧仈冕䎛挱春\u0b8cᚘ畢壒㦑妩㛒䘬ో\u171c紲娈▅୳̀\u2000夂㤰畫勨䶱࠳挃䘅ോЀ捭䣮㶽ᮓၗ׆\u0b8c\x1b眇䣂㆑ᬫთ◆ฌᤗ〭灜䒸ᇉ儠沭ᡚ㒷浳䫎ᖹஓ睆湍䆜᠘㈮橜㑈嬫昖洭孜㊳敮䋤㷑ᮓၧ䘆ಋ᪗\x00䐈ㆅ㭫挰䙅䰋᠕ԃ䋮ㆥ匋因溌ᯝ㖹湩\u0ace㣄熁ጂ怀媂㤲獥櫞\u0dc9ᬫ§◆ഌᢗㄮ扮〄挘䛶洎壗㜷楦ӎ䰸⭃ᝆญ婚㜰潣䫤䰝ॱ挃إ䌌ザ湩䚾֡獳䙖₭\u0b8c\u17180ሄ喐歫囖ⶭṛᢅㄮ婰㣄熩䌢ⲁ孝㲶档峂ᖹୣ̐恀峃㠺汰嫊㦕ணᜦ沭䍜\u1718㠱摜䒴⥱ዣ晦宁㨲潷囤䐅ခ⃠䲮ᩙ㊷獤廨\u05c9⬻ၦ◆ఌᤗ洌勂綹䌚昖ⷍ嬙ᢀ\x00嘐㦽\u135b䙗Ⲯుᦗ㌮᠀֔䮛\u05f7洮嬙㜴\u0c73屢惄ᅱዓ׆\u0b8cĘ挆擞䷁挫挐إஎᚙ⸱屠\u1cc8⬠ᙦຬ崛ᢂ〮恜Є@㘗\u2d6cᥛ㪷\u0a00䛚ঢ়䮓癆沬Ŝ\u1719⸰f倬፻طⶭ᳘㊺ٲ灢䒸ű〃污᭛㤸獥勦㗕ࢳ䋣䗆ୌ㪱汩峈ⳤ᭩挖إஎę瀄峒⦝熈̒▧\u0b8c\u171cర勠ᶹ\u1afbᚆ䷌ᥛʶ䥐ຜӅ怐⚐䷮妛㤺慮䫆ᗍ熘挲إᩅ㞹普擪ֹ⬛眶ⷋ崙㞻歲戆䂸\t傰汭ᴝ㠹潤擞ᗍ熈挂ۅ䉀ㆶ晷峊ᖍ⮛挐䘅ോ\u0b00畳䫠㗉ጋᝇ䵍ඛᤚ潣䫤▱㌓挐䘅䱋\x1c猋嫒㇁揋皖ഌ䕝\u1718㠱摜䒴ⅱ⋣䖦嵘㘴\u2e64扦ᰈ笐ᝆⷌᡚᢅㄮ屰㓈ᦡ䍃ⶠᩘ·0ᘀ■䌻ᛆ೭崚㤲䄃㊜ᐅΘ☗䵮䆀㪱楲曞䐹ॱ掃♅ോ᠗㜮扜㐐䬋ᛦؠ䂀㠄瑡僆喽䭣Ⴖ◆ฌᤗ㜭屢Ⴤ୨暖\u202d\x0ć慣䫚\u05c9ࡣዣ䜆䲋ᢖ〮桜လ㌫嘖ඎ䅝\u1718⸰ɠ㠀挐㛶浬ᡘ㠹湥擨⧥熈֧̒䮌\u17190栤ᖡ殓䘖䯭寙㜺慤勨㦽ࡃ拣旆\u0b8cᰙᄀ僨䦕୫盆ಫ尞㜰楳峞䐡ㅱ㋣◆ೌց楬峄㦽毋囶\u2e6eಁᢗ〮䘎֡獳䙖\u206d\u0b8c\x98ਂ壊妕⌋⛷മ䌙\u1718㠱摜䒴䅱䋣ↆ塛㜴损䋐㦹挫ဖ\x06ǀ㪹敮勘ᦍঈˣ◆䅌㮄牯䣘ᆕ⍋〷⺬䁚\x98椈棜䦕୳ᛆ☠䂀ㆁ浦渖䂸ű˓⹎䲙Μ敮滨䦽\u0b5b̐@ᡃㆹ楨䫨再Ꭻ林䚀๋ᰗܴ䫜巑፻ᚷ☠\x00㮇楥䣤㦥㬻䘖ⳬᴙᤃ㈮扜Ä桨瘶ⳎᲝ㒷畴䫤ᗍ熘挂䘅ɀ㤺獡䛐㦅㎛挐䘅䱋Ț慭峒䐅\x01傐汭嬝㎴瑨૦㣄熁̲愀嵘㪱扭擊吕ॱ⋣\x06᳁シቤ屢惄ᅱዓ䗆ಌ᠗⸴橢\u0984倘ᙖℭ䮎\u171b⸰恤᳤䌘昖ⷍ嬙ᢂ〮恜ࠄ࠘♖\u20c6ౌᢗ㐮娈▅୳ጐ@孂㖲湡曒ᦵƈ⋣◆䈍㊶慫勜㗍࠳挃䙅ോȀ戅壈থࡃዣ䜦ೋᮗ洊壪◑挓㛶\u2d6cಀȀ業䛦䐅ခだ⹌ᡙ㊺〇橜䂸ⅱ偆Ⱝ定ᢀȀ渒斅⎛曷沭䆜᠘ㄮ恜㠜⌫睷湍䃚\u17180ఀㆌ殫㜆Ďஎ\u1718⬰恢栀䎘䝖ຮᥜ㠼牥嫒㦕ண㛆ಮ崝㜴獧戊䂸⥱#污᭛㞳瑲᳦㣄䆉⋣▦\u0b8d\u1718⸰ࡨִ獋ဖ䀆\u0380シ畴䫤\u0dcd死ᜆ湬䒜\u1718㠱摜䒴䥱狣䖦ᯙ㎹\u0e65䋜嗑⮓㜶ⷬ尛㦰ͳ屢Ӏ瀐䜰䷮塜㊳敮滨䦽捛挐إஎᚙ⸱屬ツ୨暖毭娘㜰敮˘Ä\u2000♡Ⱞᥛㆲ浯䋠再ጣ瘗䲮᳜ᢅㄮ婰㣐熉̂Ƞ奙㞱慲勨ᗙዻ盆汭峚ᤂㄮ恜⠀笐ᝆⷌ尞㨷ٳ屰㣀ᆉ〃ುᢝケ正惪䧍࠱ˣ◆\u0dccҁ潣僌ൽ፻ٗ䘡උᨗ㈮\u0e62ᖜ⭳ᜦⶌ䱀Ā洈哆旑䭣㘦䘡ో᚜⸶屠哄桁☶⺍嬞ㄴ\u3103恜\x04䡀ܶ氮宝㤲\u3103恜␀㌨♗漮寘㠶ㄌ扜㣠榑挒䚥\u0dcbԀ敪棒ᗝ嬋♖惮\u0b8c\u1718⸰p値ጫᜧⶌᴚδ⸰ᱠ㤽ሪ僐䴭ᩛ㎷慧仈冕㎛挐☥\u0b8cਘ慭峒㥽⌫睷湍埚㐱湡䫜ֱƐ䀠䱡ᡜ㨳睴䋊ᖭ㮓掐䘥䱋ᮜ洄勂ᖹ熈挂\u0605䂀ゅ慫僦ඥ箣囖\u20cc䮌ᚚ〲娈▅୳̐₀妁㤷敧Ȇ改\u2062嚗湌峗㤷楴仜䐍ű倃\u0e60嬜㨴\u3103扜ࠄᡰ䛶淭峜㘰档曊䷑ࠫˣ旇䌌㐱湡䫜綱୪暖₭\u0b8c\u1718İఄᗌ⭣囦↬䮌ᰘ㈮扚䒸熹玒ⷀ崙㞻歲戂\x00ₘᜦญṜ㞶摡峒䶝ጛ噗ⷌుᬗ㐮ᰆ䦌㌋ᝆ淍崙㊻歡\u0ee6ᖸ㮣⛷浮ీ᠗Ѐ娒㦥ᬫᜦೌ䆝\u1718㠱摜吨፳癗洬崜㤲䘄ᢚӍ၀癗洬崜㤲䘄ᢚӍ怀址乌ᡜ㘱湥䫈䇉熈̒䗇䭌\u1718⸱屠䃄Ƒㆀ෮娜㦴楴䋆ᗑጣ㘖൬塜㖱癳Ố㣄䆉⋣▦\u0b8c\u1718⸴摢Ⰰ筨㝖ಮ川ゲ獫Ȇ改䀒ᝀ⺍官㪴խ屦㣔㦱因溌ᯝ㖹\u3103恜Є倠䘖ಬ䍀㤱慥䫨巑ଫ嚶์ಂ᠗〮扜ࣜ⡰㘖漮嶗㘴慬䫎䷉\u086bዣ䜆䲋ᢖ〮扜᳀⬠ᙦຬ崛ᢂ〮恜ࠄ(ڗ䲮䌞\u1718㠱摜䒴ॱ勣æᥙコ汵૨㣄熁ጂ怀婁㊱敢令Ѝ䩲\x15ು幛㐻敥Ә㐘猋䝆䲭ుᲗ㈮\u0e6eᖸ㮣⛷\u2d6eీ\x00攉廆㶱䬻㘶₮䮌\u171bȳ戊ו宓ぶ䗆䭌᪙и䋚㦥ࠋ\u2003ƀ塞㤲浯峒㖥̋⁷䙆䱋\u1718б䋚㦥ࠛˣ&ƀ㒸灧峊怕űዣ⁆如㦰扴峊\u218d〫ˣ䗆䇌㐱湡䫜ᖱ熠换★䂀㠄汯嫲䦽䎃Ⴖ◆ฌᤗ〭桜ა୨暖\u202d\x0cԀ畡廨ᗉ挻⚖\u20cc䮌᚛㌵ᰄ凌፻瘗ಬ岙㮰牥೦䃄ᅱዣↆ塛㜴损䋐㦹挫ဖ\x06̀㘳硵䫜巑፻㚷惮\u0b8d\u1718⸷p㠨笫㛦⹌ᦘ᤺㈃摜\u2008猨♖Ɱᬙζ⸰ᱠ㤽㨪因溌ᯝ㖹々恜䂸ခ႐ฌ嬜㦲楫ᣜ㣈熡㌂涥ౘᢗи狦ඹࠋဓ䅠ᥙ㤹瑩䛊䦽ጫ僠෭ᵙザ牲櫞ᗑᮓႇ◇䮌ᚘ㌹娘▅筳ص䰭宛㘲㈁\x00䡐㌫暖ಭ᳙㞺慲䫎ᆅ笣㛦®\u0b8c\u171c2帔ᗁ捳ᛶⲌᲙᢃ⸲屠ࣄ⁈嚇䯬塝㘺ᅴ屢惄ᅱ⋓׆䮌᠘㠮牬㠜⌫睷湍ƚ\u1718㘲恜Ѐ梨䛶䲬宜㒺昺櫘㧡⌫睷湍峚ᮁ㜰\x00",
                "fmlNetworkVersion": 3,
                "mods": [],
                "truncated": True,
            }
        )
