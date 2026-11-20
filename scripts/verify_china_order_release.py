"""Narrow owner approval, 2026-11-20: supplier examples, NOT auction lots or third-party license."""
import hashlib
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
IDS = "001,002,003,004,005,006,007,008,009,010,011,013,014,015,016,017,018,019,020,021,022,023,024,026,027,028,029,030,033,034,035,037,038,039,040,041,042,045,046,049,050,051,052,053,054,055,059,064,068".split(",")
DIGEST = "c8a31991d39edb5921295bc4f759b9d97d04136feefa597999b0625868490c95"
PREFIX = "assets/china-order/owner-20261120/"
PAGE = "china-order.html"
EXTRA_PREFIX = "assets/china-order/owner-20261120-batch30/"
EXTRA_HASHES = {
    "049": "9cc8b3627a88dbe6ab24a9259239872417d1d12e16bd46927833b52c2dee41ef",
    "013": "f99491a6292f3bf6987cd5f0593fced3a28aeb94e97c5997b7239fc60a11068c",
    "030": "32fa7713de1ec142183fe1b5f2547f33bc335ec543d5216214213d3d9cb35375",
    "051": "f8f252aba4939e4a4c0872bc99904f3d4d46e96ed3a9b89dffa7dec46a2cb79e",
    "064": "8d4fa2271eca4fa59d97a219e770dbf9ac625acc1501a02beef47e95d796d1d1",
    "052": "4f521fce4a2af1e913310962849955eadc470be4d7908c9a067183ab7632443b",
    "011": "16c7e2322a89779dadaeb68b9266e8dd3775978ed5d5fdce8f81c10ca1864eb1",
    "081": "39a974f57441eaf3b47f975d2bb0ac8013cc412c2177a8966005e207e646487f",
    "083": "89e3a8f6e1e42b26358c4ca2c700a3a879bcc8b6d13186c10641c3fe17dca0d1",
    "088": "e661dfa9c20c59692140c522dc6d50727fa954446a8de20de8fe7c97d7c2f6bb",
    "082": "5e557b9c77466545596e8f19b9b93709f699b6f0364e2816a918c86749d6e7bb",
    "037": "63324f32ea7777bb3724f44944b635e4767584835371a1af53cb59ceade8d8d0",
    "054": "65846e2cc3da448e3b6deebd8b9fec29b423ff08164efff172053c304254e764",
    "077": "d71897ecd32cfc7a8e4dcc8c65a492efefe29ec277f1f908b5fcf1f44b577362",
    "078": "73f7fa63034bdea21771b775a5a7f4a54554dba4cac9699d93bd4647582f08da",
    "080": "0c8acdb314a5521163148eb32a2c6265eb1e1cde5cdb8ee4e1870aafadd4feac",
    "044": "1f628e517f38e6c4471be6a3a512a90cb8d10ba201868cfbfb89794d3ed62db5",
    "045": "9a378a63b91441fdba14cab09ffdfd58aa2d79871c759af40758c35ca33c46ef",
    "055": "12bbbfcae224ac0231335a40bf2111c75c22d27567034a864e8fad23f01ef3ad",
    "069": "4e35cd9f25c138761f83914fb3e6286a4ce700361b404782f3cf8ce947f5dcbf",
    "007": "4143243792d184ffa335527af42d8a52eab5b5d6495f2ceba716cac7332bbf69",
    "012": "849a3ef6159d788083945442e2090c68f30a26e602857911ed9bbb4d7f4d57ce",
    "018": "cd67edf5728dd0030d09cf3839ed086e5f3458fe26fbde33f8b8cc0d1a06914f",
    "021": "5479520b49358a815c5c98f988b794b28dd4f10ba3c281f7a168e9c6242ab5e3",
    "022": "76c723114bb5881806bdc3404de94fd140ad0c4e855cdc73ba9e81b391b8143d",
    "025": "24a8d116c3abcf313b2a20488f99fa7049a4934555dbc2ae493acd0539ef6878",
    "027": "dbf19b7a67e1ad0e7d342652754bd77915b4362e941bc9005b183606272c3793",
    "028": "638dd31d2c02a4c992258b1a7793d0ab4d2a91947facaa19e394fd9d06bce3b6",
    "032": "c1bac8dc045981cb3d8a217a136698c90cbd7bbb5a82ebf0973c478559aa63b6",
    "035": "07546e4455314988c88bec1c96ea23f41c57dee61b1d67cfecef975ec33287d4"
}


THIRD_PREFIX = "assets/china-order/owner-20261120-third30/"
THIRD_HASHES = {
    "124": "95a14821eddbcf739f27f24a212ad6e58c4a0b890c8d6a50deb6281d6b6c466e",
    "177": "e36d4e7e3d7510b94d8540504f2d88e7e0098c02fa7c932f654f461b8a8a15b0",
    "134": "95328985caacf48b0575c789cb6283951332e14acefc926352103d59f676c4e9",
    "056": "bf1cf1c5728ebd40dafb0e63a63884b5b82b61ca0a4777c3601814e5458ffe95",
    "116": "fc6fee34fbe19babc2481987670a5f662da516888bf1e4c7fbe107a516643078",
    "072": "f3558e0bcce84be5d4e14e79b8567676fbad8975aab8a1bdb70d1590da119cdc",
    "101": "2b53dcbc1369c989df66c8e749546990ad82beb66958c7ba2c57e8ff65f5375a",
    "054": "a848911a77c79a497f266992d5f389fc33d5384d0f70e143d2d4e904beff766e",
    "044": "c5461ca653ecd0e1952a4db04e540dc6eeae47acb549319097fdf62b528a6f70",
    "019": "48e726429e4c77fef0c648ac03c2fe5b5b5647162ae76cb7f968fa2204cd7122",
    "005": "d322a85532a59a3b3fc9b6b8eceaa331d02578ef82fe0df29505d1308ee33b8c",
    "015": "dccdec908ccd94f6074fb67353e5b0b1b99b3d0f69ccac452bb5475121a3cd9e",
    "113": "ec8d10326e2c8168789a6d5f4f493686af8292588bce29c04c128d007eafe6b6",
    "060": "58b432501a7102924cbc44a97a79b4e69d899037f92ab2d1187c8931b9e63996",
    "011": "535446a3e2e9ff9da3cd550a1d7aad93d267db6b3f4ab4ca043a5616af927d19",
    "137": "f618313bd175044dc8ca9ec2b3826b931c2e68c3061aba715745a465936a32c1",
    "026": "44b09ce706dd49d68311ec7e86473c0f41d609f9672cff3b226655c9e78b30eb",
    "066": "b27e2ec2bb7862562582a7253faed6eb57c5d215d6f6378442313bff2af5dec6",
    "023": "ec5a4ecab55717adc540d432ad989df3ffd074c5bcedfe7372bcc54cc1e05de4",
    "080": "2b0337288f0ce9db8a38f80832ca5e632cdec38c0797d7519b1129a5fe1d731f",
    "209": "02301942ee6e82915460ee5780fd2843e4ce9fe7b65732ca19e67682214a581d",
    "039": "b9a0c67369f7189782718b1fea6cb7ad69017f65e56c490d4f29a402c72d5829",
    "048": "f7efb03c29b9d8096c8b776fee3317c7fcf69724cc4b07e56f28a45af4546d68",
    "074": "d2cbb1d944b6fbaba8cbb5fac846107a6e395180898d1474d507f56b1c7f0d9f",
    "109": "6a8b57d71f008777d1a83ccabf4272296e60e6ba9cece3eb49100e67f731b6cc",
    "145": "2026b3716760ca169750b29b23c248f2a61f7e6002272807be1b87c9722f7c4c",
    "293": "1c2d93ec0f716f0ae909800e817b869f11c3dec069ae3d074103687938b7fd2b",
    "296": "193ae9532e47e3fcac513d80d7cd50207ae2857e213505f9388733d8a3f15f52",
    "082": "7cd396e9f96cac78d008a1765cfc44d27d61121fd3b25d9e1d537424884a17fd",
    "046": "4b343f5e8d8aa25b129f0b5fa613a83061ad3cd04f791f8d8173fdd9dc2c71b9",
}

FOURTH_PREFIX = "assets/china-order/owner-20261120-fourth30/"
FOURTH_HASHES = {
    "298": "42d9e55fcebcef563236c94e910006062bfc626a6d9140da47c37b147bee0405",
    "237": "de28f3ee3bc51d8a60966ec63da85061d6dfd428daa586208010c0e65138642a",
    "202": "697b651b52a8bd099b711065ffc8497dae705abde60f68581ae0244fed7d7b1f",
    "238": "4c27171798d161ce30f304011ce9b36e62ea07e13026436664bbb0b3c8fef6fb",
    "239": "2882b672e0fb293f9377d37aeb07fbdac169b55d2b4c930e84b2c51c204b22fe",
    "236": "a516f43795f870bf6494e2ffea9a256f531cd223eb00034ec6bfb3391b5d6d1a",
    "178": "9c2e4774fe83c4c0a19e696392dee3f6be8d70bccf6b04bc2387bb9240626f8f",
    "295": "781a8b9850e203dcd1d2cfa28538521ff1f376a999e47543cc2b082776901ece",
    "243": "fd0166d6c056013721037c6519fa2830766411a30638eb986dc49a2d4417e101",
    "294": "4b25a71e942845e0c6fec4ee180f3149583b5f3155a238a71b678d2c37140676",
    "093": "911476803f35a715543321e3735768af8d02f37b9e8fc55d1093e384f6f44177",
    "208": "2863a07186025138de824d7f764db5ccc77461c4c8e7b0ddef3dd39fb9d0883e",
    "165": "2bfadb07e14b0450c01c9e7c077f40961a277f46ff2ba2ed5f11b76a72ee4e9c",
    "205": "0f64f85db25105b93fb37962df61fa0d36943eed5911e72afdb40eaf3ad31734",
    "085": "ed6ebe11393fab53b9047e8dc4fbd4e2e74762ed335e038938ed2e4629fe5934",
    "189": "88d55502500013fcae1a2c67e78317fc5e901673ec191ac02e6866f04dcceb71",
    "226": "f7930d2a8fa691dfe052a62d3b5882da95c66414ff66bf36b4fc895ffef4bdeb",
    "231": "23a397a7a671abae137d402720801eb8d0ed0152fd369bbf1a15d7eba599648d",
    "174": "8f323f63ae9a621e6ae4fd516ba175901e92e7f058169b4d2897c3b0a0e455ff",
    "184": "4c54abfc9d6856eb36733fd7f9974d93cddd51fd2bf4510c5ce534efed904422",
    "198": "4762e527dea61d123cb013332fbb64c9dbc4d51e514c1e422dc84c50c7b69cc1",
    "030": "7a62eee15081682bc39a19d92f85a00e96c7e88be5fbb8397089878ed5197d68",
    "163": "f8258ddbacac66ee8e736c75393061d0aff80e18c20a6d56271c75ba2f7e540f",
    "214": "c148af6ff7ef9e1d176d9d94c0d8a7e703625e568c0fa31ccb23f1e31fd8cf81",
    "129": "c533af0676f3fb591f2c5ecb8817379a53081d880954ccf4e527076661b1b6bd",
    "218": "22755956c554510d6db50fb88f4bd43606b5245a417ba098375495330b84bc38",
    "180": "b503472bc42ef1093ff670f86b1c1ab72437e4fdab4966d6f5334e1781601b7b",
    "104": "86b28274fce0bac77ae01ebee68841dbc9aa82f370e5efda16468a2f3c701816",
    "249": "be222eeac8b743d288b4bc517c1683717a678597af3e0ba381c6ee5748aaa508",
    "007": "3fc72520ec035986a649c564301bef0dc497c18f77e15f88bcdfaf68cc2fa8ac",
}

FIFTH_PREFIX = "assets/china-order/owner-20261120-fifth30/"
FIFTH_HASHES = {
    "175": "3272cd80838c3fe1fbd1f54aa68c374c13f10474d632a5a5e8252629269914fd",
    "223": "6c6cacce807e29a6712b4d71544f7f171db280e026105172f77dadb87fef6486",
    "240": "30e58a457e4d5edc21dd4b5231736187ac0d7a79483edb75e607baa33c3ef626",
    "244": "e2b7369e11076e25ecee549e30100977e40fb65c14908d13317147f9ec3f5062",
    "126": "d9e84abbdeced23981a243a1daeafeb76eb5cec6457c5e5337617f7f37485532",
    "288": "219803eae86684b8c1bccef395ec263d5517b47e11744fab0ae21c5c8b9b0adc",
    "289": "e1a703bb33a352b05e1d527c67e0cef2700311d6bbf76941ef1a9d853f46c032",
    "179": "3a600872c69b34a6c640dc8b6b551e384578ec839638b4a647b6ee919e5f44bb",
    "150": "294cfe47037688cf64d2c92f420368085290e302b5901cb16290459c62ef6c2b",
    "168": "ed64b08b7b6ccd98282e7fe6809a7de10a14163873180a54e45b37a11a7f42ea",
    "181": "df5af2a709444a607d7a5fdf38f206cc31fa9bea87d87c054a80ef32309b7dc3",
    "207": "ea4d51855c925654f33531840351289768f6e6e870fa7d862389fa600b135b6e",
    "216": "2d6d5ee274de826d37db56b10dd9e366261c3cc3810196d60d0e60acb196004a",
    "221": "b59e2cdd813833374a3133f9bab4984153b764e7b0f94134dd8898cb0aaf0041",
    "228": "967292ffd6d95a8c034db8850c0b7d60f4c90cf45d40ce9dfb1cfe831f3c1ced",
    "232": "6ba84a03071322f3f00bc08a7a999557e2f9fa7167a48aa8c87e67f3aa1182e6",
    "233": "10b93bb383aa0165684c667f8576556fe27fe1d47ceff0340dd2bfda7e438dd6",
    "235": "b735beb4142e8a700e5d5c1b101781462678a9ac20209b7885a05114891e250f",
    "246": "126adf220a4c43b8279b759f434a0572803d61a0e12c45cb7b4ff5c7ccaee3ec",
    "247": "8591d585ef3c97038ee0242c096b8bd01406a485ad857dcc061734fc730c324f",
    "350": "cbc5890f09e7fe5bcd4b4e8f2391d3a93989647e3a75169f58b062df203dabe6",
    "133": "a654a637c726cccfff5aa17543b09db3ee514243aee0c736c9e7c7ad266f9e78",
    "166": "4f0c21f36ce033b7a76d730c401617f99a9a8faa12df22fe278b7276957987d0",
    "172": "372f4a1a50b6609a0d11d2b088fdc2866e0a65e1e5877de32d5bb322dc97f002",
    "194": "c074a2d5a90ca5f62293a67908267b02b0bee3f5d9e48757e582f5bdf7a4ce83",
    "219": "d414beb09ac4e48db92f0199e9f728ba3a8dbc3d849d6254cad67d8ed0ffb8dc",
    "241": "457c3d49da7da378cc1a62481e1ef40fe2f0daf3c525d189f3579f53b84ca664",
    "290": "a06b4a2ea40b4c216036c6b815ad79e910859d44d022cdcd15232dc6f8f9ac09",
    "120": "8ba0e9dc92b2f2821dd621a7445f9c0f5974e74851cee146e3bb825f7f47960a",
    "002": "061dfa32108e5137f61397d62652b4e3e4812de3774998c4da0a32bc0c72d8f9",
}

SIXTH_PREFIX = "assets/china-order/owner-20261120-160hp30/"
SIXTH_HASHES = {
    "001": "5274127da61551dda0d16a1ca65f87612853226d42d6493676835e758a36a0e5",
    "002": "50e618044b77778ba31ebf09e864569f459a1ec002b5a1595a787e464e9ed933",
    "009": "fd9cbccad02833bf727095f050099bec770476c34363bc2733050e5a8be3a54c",
    "010": "62567f1d72e579bffc6c9e5d0e6c6c1ff2f0483410be622c75e351c0a4a4de62",
    "012": "477fe2e18c62f77f977b8038eb307604b70681860846cea1c61d9482a2c72068",
    "021": "f750270258712aea947705249a180df91ca096f59b13b801f371d01355ee34aa",
    "028": "3f0371608374df412a2cebd0a876f598a7120160f6856d5335d638a8ecac5a3b",
    "041": "2e42663f35c0b83107488083314d2c897c6f1801731935bf32cffa66a567124f",
    "043": "03f4ec24a9eb8a05a65a403b7754181a3957d9e8e917d752ae1fd50214ca815f",
    "045": "68f0180834d0f5b4a0dffec1da71374976d693b1dc550a12191d3cdbef1a6d2d",
    "047": "46b14e19bbdb4e01ee68ca8fc3c4a2cdc6e323b1c9efb74b06ad76e737f37ac9",
    "048": "e8ea9049d4780d7350ff7a22c154a1efb2e1ebe6b3d6cdc30af81259fd3925fa",
    "054": "c225273e483a5e5442ed02559e37e92f1b72e5c4e84c162364b68ad85e4f0314",
    "061": "2bf869729781018cbaa5f795d5c032b1312470c2b0cb5367ebd41b8922f977cf",
    "064": "1a394bfb9d522046ebe88527f465dedca6eb6c45f6233137d4dca883cce36565",
    "065": "bcdff11a8e80a0c14ecd07ee1d38fa9619c025e8ca48fd9f67db367fab8dca68",
    "076": "df0aefeb29373a47a4b002a233dbe7d5752cf1844a5053ccc5eb2df4f8eceb04",
    "005": "07776d3379fc8afccb811930b2d44b901c8a6aba087002f2f5d2ca9407a70a4c",
    "011": "e8681a043460a09fbe7a737f2fcefc4158fdf48ddea74a2054853b5f4a3c25fe",
    "027": "512f11e94a1f2a47c6fe0e8748115cc5ed72cb24a12922c4ea7ca9ed89e1d06a",
    "044": "fa7e0a949251bc8285b425811b365cee88218efb4fc7c55ec175205cce3381d0",
    "046": "fd48e6731f83bb4807d63b0ee9499b4341f8b6a99848f973cdcd3ba8495f9249",
    "057": "1b19a8c421570314ea3c9fe9b3ea4c51d16152adfd5507b0e4a5121ecb50c5ef",
    "058": "152a8ff403e81210331d192b7aee365995901333612c5ca167b92cdf2ac4177a",
    "059": "d11740eb0adf33fe6db5a4ce66ea57dde02cf1dc8b523a1a614023b038f62d51",
    "066": "0bf68277a53dd12a9e269265de8418055d090e659f734225ab246e2ce1190e42",
    "067": "20471b66cb518cc543cfdcd1e19120a7799d2ba0514113ccd011566f322e5428",
    "072": "53244b605e7fb4ab07a3be1a880142689bdf237727fdc0fb704497986a7de473",
    "062": "f0db36409ccdb74adec12ce3741d76743c4f87dabeacca5766773f48b83979f1",
    "060": "b56770b8dc6a1aa04758bc0f789ead61f6e107376aa653226e8277aa72325606",
}

SEVENTH_PREFIX = "assets/china-order/owner-20261120-160hp11/"
SEVENTH_HASHES = {
    "006": "5a9c03b77d907f410a7a4b53ef37f55ecbb95d28a8cb728c0046657235dfd9c2",
    "026": "f4d173e93ce6ddd7912b920bdfe133ed93c36aff718da2a7968c57b606675de4",
    "034": "aaf23f483195d160461a7f6da81ff55e730337e107ccdef3595c9122aa76000f",
    "039": "40ca4f2dd662644d28da3d62153b9480b03921eb002347b85fad5d3e93ded47f",
    "050": "b734b0c657bd17723a9c0535e17059bd20a37869319e67661ad2c911e8fe7f48",
    "051": "0a4d421e8361ccbc556b34655748617291e66802b3c2a3b059a1dd22e1d1e6f9",
    "052": "e8463b9247adf08bc2a76b9d510944772e257a3cf9db94e98c888fa222150df0",
    "055": "d9ad9185eab3aa5d9c5eb1c1f3f67932f3eef24e886273b2ce6480b2f693a2a8",
    "063": "e4ebe77a1d3b8882c447b77a8d712b41a1dd299d7a0998803827142a5fc194a7",
    "001": "b1b72ac6b977d97766c369aec13f217d2ed401d3c7bc8510cb6f9d2d038fcaa3",
    "002": "4436334c1b5588e617af8ab21ebb5e4bbfbb2f16781fb1eeb2d1aa51397ad324",
}

EIGHTH_PREFIX = "assets/china-order/owner-20261120-160hp10/"
EIGHTH_HASHES = {
    "001": "5161aa35b564caeed7b99193c492a33253e959a376e5ca92b995f6f8fd893fca",
    "002": "5e3f1a44958e0f4630d760ebf220ba1e9fd607f5fa90280830e335e1d1c0c501",
    "003": "4b71dc87f27c067ab11d07035536c54fde54bc01cedc0c35d439fbdeb0049ca8",
    "004": "118b1cb83a8724c5d102f35281491755fd4993d9fb4a8883f471c3091ff05f46",
    "005": "7dd24c1387888482f2a40605435a683ba76373c2a12a2423d5079f1d3ecac04f",
    "006": "c05abf2d8fd690602fb2739a048f18a50b9010eedbb0cc62f886fc53a6f83238",
    "007": "aae0afa3f4f013c51e745d4841b59e685801995e78769469d02e654398f2e032",
    "008": "5e68dddc592971c30946a89d815f23c634f38fb4bddf479e0d94543a97461277",
    "009": "009564e4789528e84c0ede61f9947debaefee252115024a62be004ce2810c363",
    "010": "4c65d82c98d27c983beacd367aeeea827863cf235ac0ffcc2d05f5453c1ca356",
}

NINTH_PREFIX = 'assets/china-order/owner-20261120-goldenlane9/'
NINTH_HASHES = {'001': '5fc3ce76d0c03b72ccb93a30b69ef6f8938eee5c058db84304df0f1fe725f3e5', '002': '24ff376223b6199ba14f16bb0bfd25fef2ce34f5e0bb2871dc8340170bab4774', '003': 'b19aed4bda81508a3cd9c6e92414bb43719bd9e288b9f02df7f519c156967369', '004': 'a46027aa6eb86bcc84028c1d118a6b70587ad8a19c54c6f381287d7c377c0e68', '005': '963dbb4786c107ca7dfc82797886b9aeb18b63c8bc6fe9080c858146a114244b', '006': '8a1bf94e679bacb2b8c14a70a1e486d58066118027244b8eea727a71177d1bf0', '007': '511124b6e73cd6c38b65f91fba6e3ef88c37d16577b25c691fe49d8950d06b07', '008': 'c8ce41800d791f663d4d13f7767bf988d3c1e938039b771db212e7108684442a', '009': '141755eb86cebdaacda862e47c69717c12ab71ca82d52c86ccd20165c60c434e'}

TENTH_PREFIX = 'assets/china-order/owner-20261120-next30/'
TENTH_HASHES = {'001': '00f69e2203f1567d8c3473bbaa577911d65470e71553fb09f4ba8159c1df6f6f', '002': 'e3fcdbe072f271ca7bc0de7a63b7692bdeb4a2da3ee09df58187cfde437a57c4', '003': '0f73c037f61cf0e188e5b112d19860a2cb30cfa9ce54ceff043fd012bc55ca4e', '004': '5bddcf1cb0ef44a5ee244e8302c9999abe12e8393d6e52c4cdcf094ed66ffaed', '005': '286dfedaf612cc79a78d89c69bb4a1543b16b12c4a04a69973fbae8ef9db8499', '006': 'bd1cc42b9d2bc1ad72a23609d629fc1ce6212ecfc1b44079b66a727ba5e5937c', '007': '77f2c0382d1aa0e97de8fc9ade4b47c1c35f664b401c85031698eb14605f0585', '008': 'adc65f426ed3858aa5d687902839c5f4d39c2538e1289b017b2d04f49e037da3', '009': '778fe286f73c75c82dde44715fe9b4c35b31fdd408dfb6628a8faddedc9a8fb8', '010': '52044c54c14734a65112fec01663e2bf389750689f808c58e00925710988fe97', '011': '7118d713b42f895c665dc26cfbbe6937a906cd8d182f873e189c76512610df08', '012': '2b4c1a001f667b0e8fdcb30b6fcd599ac5965452c5b391ac8d0c7022aadf429b', '013': '8a7ccc93559b19b18822489edb232271132d4f13546a7183c4e9ac2d2235be02', '014': 'bccbd780da715b6dea7c9d75cfcf78e8f97b9219af287d83db6b855e33be6bff', '015': '25b18063f01908fd2b200cdb7e66a33c3f9da229d693370bca12d8e41eae5a9c', '016': '66a281c17157b7e174d5d14c2e6ab7e01a8f4cad5a6bcbc4429c26b24f062beb', '017': '0e70f217814ad4e98ce58d5f4a8e4e59cf95dcabc1ece1f646f7c6022266580a', '018': '995f3e0c55d2ed5580e3151e09b9de2783da0c5ee6e2ee69ef0b25cc4ebbe408', '019': '8354e6372522037df1a5f1c2404eb1aed5ffdd2c83d46ef417e80ccc442a116e', '020': '9eecc7f79b6a57aafb0df5998767cae00ac38221a7fa3ca9d76628a0efe4b805', '021': '16e969901e660506db5977b3cfd59c2288658b43f3317a69260d3f928cced144', '022': 'ba15fb08f3025976ad27dcd960abdbe484af383a08453a1e397180b5dfb2f5b6', '023': 'f8b6d6fc3c9c225c5e1b7a78d78c9162977725707c3c1d2e49dc3bb85e2b57fb', '024': '2a8757e481934c46ac8dc3440fe59351a50681494ef1f5df0eff646a2188022f', '025': 'f0ff8302d74a329e2dd2ea4cac3dbf42c8dce10665731bc369a1134f4c047788', '026': 'c8f8188de844e106100ad1c08419a23c34a7e0102a96268f85d91007c2c912d1', '027': '497f0dd535db4d5f0cff8ed471fe6964f717c0ee58879dd7d06a923f7102ed1d', '028': 'd9bcf2a21f80edd319e86b556f3b848460d1d4db0e175fe47b9404a375d48a62', '029': '85afaec9aecc05c778bf2b3d06909c3c2a4adadd9ce4d804bcaf46205445717d', '030': '423fdd30009fd924b1f118c6accf4bfb7adabd72533780d2b393fada3165cc55'}

ELEVENTH_PREFIX = 'assets/china-order/owner-20261120-batch11/'
ELEVENTH_HASHES = {'001': 'c601207908f7e7493221d76aca560fbf21fc9e3a4b85465231690b621847a9bc', '002': '10970ab698c661a727b6cc4ee04a3ac8c118298babd408ca94618c6733743359', '003': 'db3c0914613fc2c8c54016d407733bd928b086b44a10162015d971e4ee41b837', '004': '684577650068724b5b4af8f44d500de58aabf4c24264d86839a226b7b22a01de', '005': '68fa894f4b770a584b5051461c051e9f208a93b9642010c5b36abe2c60a111a9', '006': '2db1974e8d8304a15b365478a48f51ebed02c6728d7b143ec939e2ca835b5891', '007': 'd0fa21b559342d64f0e5cdffe3a6c8c42cdc29637629070a3658dd1b7265f649', '008': 'c121e9c3d701e4123ad10a8878f8bb3de566ce0c945e4d2a9a9f287830127a64', '009': 'd970cfe49068de06e4d6214c21413c5ab126997a83fd47aae0f7a734ff3c51b9', '010': 'acfc64d488ed0501c8ff718cc0e9381453cab744755a5384b8b0056592cb7c4c', '011': 'fa4b7c4753daed94984e031b68106f0de8369c9974d3045c4caabb399be59d52', '012': '08d077ec5c918d20b702921e7fefb068e5045c477c5e88149f2212eb9584f0bb', '013': 'c23fffb901e52354573f51482856ed87d7c66f54f0658bd993112117aff1ac00', '014': 'ac51e71f737ce87dbf31dd62da86d54f313e6a5a0e1f8425e375ef34c04c4585', '015': '18d9551986eb5d22fb3046200676f69c36bf05e958ab0c8e0e15f129f5546cde', '016': 'c7749082f9d50ef09991f178a49da5fa5b65ded6a6266c11f1d0e719e011a217', '017': 'ecae62d943151b56cdec5a28a2532444dc7aadbe5ea845e6a6b6c6d8322ef943', '018': '754ca58fc73ffa64ef8904b6bcd1e10c7e6f5a02db16003080610a00f1499a3e', '019': '069b0b50b6cb859030b1798a5ac85b8d8d15ba1458018fa54b6cda5155e50212', '020': '566eb71753152459d0c061eb549c0d88d51b5b5ced68055094cffc59e7d78a72', '021': '8648c1d77eb7056bb9f560a05ac2ea61b4bd15bcd22c8e7073c66bca1bb4bc10', '022': 'b1e999e94709f6555a3c03e4f7c2291289c3507556ca833ee6a2849bb8cd9bc1', '023': '91426053e522986f05d454238528cf84152e2673ab82df4e9d023891b1001c11', '024': '5956ee0e60338f4e7b9377482e04f4f4d3acf7b05bcefa05de23509cc51752f8', '025': '4b2f8a31efeb75411b377053887e48ccb3a1424d8d5cfdb0f1bd9203653e1dbd', '026': '18e02ca609ccb9a38889541431acbb0107ad01698415ee1483fdd4ae2c32a14d', '027': 'ca732e5bc60bbc445227bf20c885df62d897f7d30149c76aaa7d659c5993858c', '028': '74dade9e5354592a787aa4b806064f9580813ccc50d5a150954ac60a96347f5d', '029': 'a337c067ee194050c0b31a27b19eae186d4b0d0aa9f11bda0d4faa9a9313fbc1', '030': 'cebaa503cd8a69492fd13b7d08db1c02ea15fc54e8056bc626554f8b65b8079f'}

TWELFTH_PREFIX = 'assets/china-order/owner-20261120-batch12/'
TWELFTH_HASHES = {'001': '3bf6e209a9c47410a9cbc7ca7195082efea27aaaf07485c71fac9a5d736523ba', '002': '64c0e5cad980f8993012d84afa46c2eeeed6346f84fd959d1c3f900e6bc58deb', '003': '1bd812399ca2ba66a24357ad5f0f1bb8bba92ea9a126e98a81f63ee91f2b720f', '004': '66f1d5f84a1b45d7fb840ed8aa7fb3a1074704d5787cd6aa4568a1c1109cef01', '005': 'abe1da0a8531c1933b3dcbf93a41dfa479b6f6feed4904e338b0a07dcc1d03da', '006': '3376dda15da7f9299800940506600ab76d1df08b7e7473dd048e8acb4622c0a7', '007': '950efb126be4c83356cb99c28893de6c0c53ed60a2f04730bf02db36a307c5fb', '008': '89bebf51f7881eacfcad66ff38ea8a71122c115d258838167d61add8a14b9f3b', '009': '86401d116caddbd081e6719a3495e3f7b138340fd4495ac5fc9e464de668d989', '010': '894abbfe93699d5f54c1b8e47b709e1309f1a36145b3ca243ddbbea069ee90d1', '011': '848b37027ebd96b9d69216a50739e95a2c39745dab38b8e4d75c9ae757a5f58c', '012': '8d8db0aec7378a41b63a2fa71a4587624f8908cd00a354ef7a17ff183be0db05', '013': '1ffaf9c366ac99e43bc98c51c30f37678f8f4dde037872156b525c3d4b82dc31', '014': '7add24219cb0c945fb87e1a17ca0f279d4d6b8867529a178538d0e689015f365', '015': '9363ffb5ced76f7fc7e3f9fc62c9883cb8004b15e3d190848be9612a02db10da', '016': '0ce653ac5a79d3c79114dec8e663659c3350edf3110b6ff10bfeaff840913a36', '017': 'd1cc6384879d8037210eb929cdc9f07cfd4a6226a0a0385c00c85b7368f2d735', '018': '27a12ecddbaece504bfd8b7161ee4edf415238e9ebcc68fdfdbc587a88e9cebf', '019': 'dfde1027acd448c4b0bad39b59a36797b00414c392b01211cada36913f8216b2', '020': 'b793b55313b770c09b9af5a80680d7399724d3585fd224492d9a160585c564e8', '021': 'd8a72388782fd0d9ea001c70e51e7f875cd32bb2dd65fcc98fbbaaab5fbe36b7', '022': 'e3eef9c2b44b13a97de6f4aab9d6db7b83827d4a4c830727ea2358a28746e26f', '023': 'c1047561d22b1c19a8eaa5b0071f4ba1a642bb31caf6bd68299fec9b4290e8d7', '024': 'c7fb07a1b7fdbab9500eaee035f564ba8a7afee5c7bc322ac4e2ab082cf0188a', '025': 'dfb7e09441c7d62c6b2cb69f619eb1cb787d1b8aefebecbd403463db5fefef89', '026': 'a5019ef1fc51e94d7bf0d12e4a88639eed0d2d1bc59fde561bdac89403f84783', '027': '4f511635e0746a0df66f7f6e5afc1f7e277623c2c7a6756fa8226f045eb3e506', '028': '2e3223d63c272aee6c006982a6ab453e0c5007725510abe59f26f8b7dc9ba635', '029': 'ef046bf09d656682ca1bdd347358fa0235992542bb2b1429d54025711b9fedec', '030': 'c640116bb7d75cdb206b169a12ccdc6f63108019bafb7af4efb060ab87b26e91'}

THIRTEENTH_PREFIX = 'assets/china-order/owner-20261120-batch13/'
THIRTEENTH_HASHES = {'001': '9ecc91fc5d58e2a9efe8487b247d1df461d4a7216c1833520ecc8316492881ab', '002': '940b21ac0b0386b80561cc66e1be1cc27d366bac105c15b501180af98986ee3c', '003': '8ed1ab1483584599edbb5429c8bfc979a6a0c8126d5e790f68cb684dbda32079', '004': 'ebb08da515c268c7ccf8bba9415e278ab257eae8bca2e7eab92c7d9641102652', '005': '175f1bbfcaf1f60da88f11c230f0d6be574348db1bb0f4495cbd06f7b2b89ee6', '006': 'acd112192f79d527fcbf7d5f64b06e252ec1b4a77558de8b5de84279f6ebda92', '007': 'db9a55134a1b5b3c53dd4cc0450b02515a4c3beb51d7e455d8d2fd7e409fa595', '008': '42b2286a44e4d01a72f6936fc448b36a74b35bf9e2166674c56a6d73ab9015b6', '009': '8c7f8e46a858f68c1db055d9c10f314f4bd06b126f50d763fbb87623b09e159f', '010': 'fb9c7043e1246591e321df0e00468a11d46703d1a36a36fb669a39397ccf0267', '011': 'f8f60f2af42c4059e263578581b43a24acd95612042e045022ce4770fff6e5d9', '012': 'c0bc9341d6c0929bc4b1b73752d9c2b09b8fbd24a8b83f38c10fbd8e14ec8a97', '013': 'a58ebe60be76aea9b191b42597ecdda921101d29579a1899099fc16c732f665c', '014': 'fba179b2ea18304dc00b36e1451fd4eea1320533584514f6111c8a1a4f591c93', '015': '781224bf297a1978194c6b115bc6f34ed38af75395c7bb4c4f9ad1fb7a70f05b', '016': '5e220fc3d99ae05bd9a3388df06641862b1dcada6773ea20ec4363d31aa67b87', '017': 'df46feb6f74463830cceb1b15467b65cf4abe4bf06474548dcb360ffbde438ec', '018': '57484cf608fcfa64c7dbb0724cf712708535e798cdd1fe1c0859266c668fe5f4', '019': '33fe2b5f89568e3e3f3600feefbbe956955fc61f00bca690fde5aa91d632c864', '020': 'd3a79de8927d38553039202127c0e5a5a6eb8b2c8dadbaf4eb002fdde4aefeb5', '021': 'b73d039d8125943e35da30480f9e7b852c131eddaf6d698c2c0f0fc64817b85f', '022': '891a9ba98a6acde45f92e662190116b8915094c988b1320a5121556b53d48548', '023': 'cad6b6a906c974f65700367401b3e1e4795c76d38b003d9c092ac98f54a94118', '024': 'd27e09278df8a4fe2f668898c8405a75fc81ba586a550b97a7459af83a6796a5', '025': 'c6dfb3e6426a0f5936d2a99f3c79b2e69957bf3cd29d9620eb01e9d3e66713f5', '026': 'e99fd391456c07dc7d8337dbcee2ddeef864e621bf95cbfbc1f59508658a40ce', '027': 'acfa50278fa14fb2e79e09d3e8aafe19a024dbc134e0a1cd2765459d30b8c881', '028': 'ee17e225249fe967be5b6ff5fe4857abc3f538444668bb3d0fc2fccb891d51be', '029': '573c156bbe9ebb67d2ecb1357f7b9f821065abedacc3f4e545176661b7e0b4f7', '030': 'f735221ebe4205d1d2a84760e29d567e57512df50d7dc22c287dd089e7cfc8cd'}

def verify(root=ROOT):
    root = Path(root)
    media = root / PREFIX
    expected = {PREFIX + ident + ".jpg" for ident in IDS} | {EXTRA_PREFIX + ident + ".jpg" for ident in EXTRA_HASHES} | {THIRD_PREFIX + ident + ".jpg" for ident in THIRD_HASHES} | {FOURTH_PREFIX + ident + ".jpg" for ident in FOURTH_HASHES} | {FIFTH_PREFIX + ident + ".jpg" for ident in FIFTH_HASHES} | {SIXTH_PREFIX + ident + ".jpg" for ident in SIXTH_HASHES} | {SEVENTH_PREFIX + ident + ".jpg" for ident in SEVENTH_HASHES} | {EIGHTH_PREFIX + ident + ".jpg" for ident in EIGHTH_HASHES} | {NINTH_PREFIX + ident + ".jpg" for ident in NINTH_HASHES} | {TENTH_PREFIX + ident + ".jpg" for ident in TENTH_HASHES} | {ELEVENTH_PREFIX + ident + ".jpg" for ident in ELEVENTH_HASHES} | {TWELFTH_PREFIX + ident + ".jpg" for ident in TWELFTH_HASHES} | {THIRTEENTH_PREFIX + ident + ".jpg" for ident in THIRTEENTH_HASHES}
    found = {p.relative_to(root).as_posix() for p in (root / "assets/china-order").rglob("*") if p.is_file() or p.is_symlink()}
    if found != expected:
        raise RuntimeError("CHINA_ORDER: unexpected or missing image")
    hashes = []
    for ident in IDS:
        p = media / (ident + ".jpg")
        b = p.read_bytes()
        if p.is_symlink() or not b.startswith(b"\xff\xd8\xff") or len(b)<500:
            raise RuntimeError("CHINA_ORDER: invalid photo " + ident)
        hashes.append([ident,hashlib.sha256(b).hexdigest()])
    if hashlib.sha256(json.dumps(hashes,separators=(",",":")).encode()).hexdigest()!=DIGEST:
        raise RuntimeError("CHINA_ORDER: photo changed from owner preview")
    for ident, digest in EXTRA_HASHES.items():
        p = root / EXTRA_PREFIX / (ident + ".jpg")
        b = p.read_bytes()
        if p.is_symlink() or len(b)<500 or not b.startswith(b"\xff\xd8\xff") or hashlib.sha256(b).hexdigest()!=digest:
            raise RuntimeError("CHINA_ORDER: second batch photo mismatch " + ident)
    for ident, digest in THIRD_HASHES.items():
        p = root / THIRD_PREFIX / (ident + ".jpg")
        b = p.read_bytes()
        if p.is_symlink() or len(b)<500 or not b.startswith(b"\xff\xd8\xff") or hashlib.sha256(b).hexdigest()!=digest:
            raise RuntimeError("CHINA_ORDER: third batch photo mismatch " + ident)
    for ident, digest in FOURTH_HASHES.items():
        p = root / FOURTH_PREFIX / (ident + ".jpg")
        b = p.read_bytes()
        if p.is_symlink() or len(b)<500 or not b.startswith(b"\xff\xd8\xff") or hashlib.sha256(b).hexdigest()!=digest:
            raise RuntimeError("CHINA_ORDER: fourth batch photo mismatch " + ident)
    for ident, digest in FIFTH_HASHES.items():
        p = root / FIFTH_PREFIX / (ident + ".jpg")
        b = p.read_bytes()
        if p.is_symlink() or len(b)<500 or not b.startswith(b"\xff\xd8\xff") or hashlib.sha256(b).hexdigest()!=digest:
            raise RuntimeError("CHINA_ORDER: fifth batch photo mismatch " + ident)
    for ident, digest in SIXTH_HASHES.items():
        p = root / SIXTH_PREFIX / (ident + ".jpg")
        b = p.read_bytes()
        if p.is_symlink() or len(b)<500 or not b.startswith(b"\xff\xd8\xff") or hashlib.sha256(b).hexdigest()!=digest:
            raise RuntimeError("CHINA_ORDER: power-listed batch photo mismatch " + ident)
    for ident, digest in SEVENTH_HASHES.items():
        p = root / SEVENTH_PREFIX / (ident + ".jpg")
        b = p.read_bytes()
        if p.is_symlink() or len(b)<500 or not b.startswith(b"\xff\xd8\xff") or hashlib.sha256(b).hexdigest()!=digest:
            raise RuntimeError("CHINA_ORDER: approved eleven photo mismatch " + ident)
    for ident, digest in EIGHTH_HASHES.items():
        p = root / EIGHTH_PREFIX / (ident + ".jpg")
        b = p.read_bytes()
        if p.is_symlink() or len(b)<500 or not b.startswith(b"\xff\xd8\xff") or hashlib.sha256(b).hexdigest()!=digest:
            raise RuntimeError("CHINA_ORDER: approved ten photo mismatch " + ident)
    for ident, digest in NINTH_HASHES.items():
        p = root / NINTH_PREFIX / (ident + ".jpg")
        b = p.read_bytes()
        if p.is_symlink() or len(b)<500 or not b.startswith(b"\xff\xd8\xff") or hashlib.sha256(b).hexdigest()!=digest:
            raise RuntimeError("CHINA_ORDER: approved nine photo mismatch " + ident)
    for ident, digest in TENTH_HASHES.items():
        p = root / TENTH_PREFIX / (ident + ".jpg")
        b = p.read_bytes()
        if p.is_symlink() or len(b)<500 or not b.startswith(b"\xff\xd8\xff") or hashlib.sha256(b).hexdigest()!=digest:
            raise RuntimeError("CHINA_ORDER: approved thirty photo mismatch " + ident)
    for ident, digest in ELEVENTH_HASHES.items():
        p = root / ELEVENTH_PREFIX / (ident + ".jpg")
        b = p.read_bytes()
        if p.is_symlink() or len(b)<500 or not b.startswith(b"\xff\xd8\xff") or hashlib.sha256(b).hexdigest()!=digest:
            raise RuntimeError("CHINA_ORDER: approved thirty photo mismatch " + ident)
    for ident, digest in TWELFTH_HASHES.items():
        p = root / TWELFTH_PREFIX / (ident + ".jpg")
        b = p.read_bytes()
        if p.is_symlink() or len(b)<500 or not b.startswith(b"\xff\xd8\xff") or hashlib.sha256(b).hexdigest()!=digest:
            raise RuntimeError("CHINA_ORDER: approved thirty photo mismatch " + ident)
    for ident, digest in THIRTEENTH_HASHES.items():
        p = root / THIRTEENTH_PREFIX / (ident + ".jpg")
        b = p.read_bytes()
        if p.is_symlink() or len(b)<500 or not b.startswith(b"\xff\xd8\xff") or hashlib.sha256(b).hexdigest()!=digest:
            raise RuntimeError("CHINA_ORDER: approved thirty photo mismatch " + ident)
    html = (root/PAGE).read_text(encoding="utf-8")
    if re.findall(r'<img\b[^>]*\bsrc="([^"]+)"',html) != ["/"+PREFIX+i+".jpg" for i in IDS] + ["/"+EXTRA_PREFIX+i+".jpg" for i in EXTRA_HASHES] + ["/"+THIRD_PREFIX+i+".jpg" for i in THIRD_HASHES] + ["/"+FOURTH_PREFIX+i+".jpg" for i in FOURTH_HASHES] + ["/"+FIFTH_PREFIX+i+".jpg" for i in FIFTH_HASHES] + ["/"+SIXTH_PREFIX+i+".jpg" for i in SIXTH_HASHES] + ["/"+SEVENTH_PREFIX+i+".jpg" for i in SEVENTH_HASHES] + ["/"+EIGHTH_PREFIX+i+".jpg" for i in EIGHTH_HASHES] + ["/"+NINTH_PREFIX+i+".jpg" for i in NINTH_HASHES] + ["/"+TENTH_PREFIX+i+".jpg" for i in TENTH_HASHES] + ["/"+ELEVENTH_PREFIX+i+".jpg" for i in ELEVENTH_HASHES] + ["/"+TWELFTH_PREFIX+i+".jpg" for i in TWELFTH_HASHES] + ["/"+THIRTEENTH_PREFIX+i+".jpg" for i in THIRTEENTH_HASHES]:
        raise RuntimeError("CHINA_ORDER: photo identity mismatch")
    for p in root.glob("*.html"):
        if p.name != PAGE and "/assets/china-order/" in p.read_text(encoding="utf-8"):
            raise RuntimeError("CHINA_ORDER: supplier photo outside dedicated section")
    return expected
