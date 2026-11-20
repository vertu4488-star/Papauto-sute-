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

def verify(root=ROOT):
    root = Path(root)
    media = root / PREFIX
    expected = {PREFIX + ident + ".jpg" for ident in IDS} | {EXTRA_PREFIX + ident + ".jpg" for ident in EXTRA_HASHES} | {THIRD_PREFIX + ident + ".jpg" for ident in THIRD_HASHES} | {FOURTH_PREFIX + ident + ".jpg" for ident in FOURTH_HASHES}
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
    html = (root/PAGE).read_text(encoding="utf-8")
    if re.findall(r'<img\b[^>]*\bsrc="([^"]+)"',html) != ["/"+PREFIX+i+".jpg" for i in IDS] + ["/"+EXTRA_PREFIX+i+".jpg" for i in EXTRA_HASHES] + ["/"+THIRD_PREFIX+i+".jpg" for i in THIRD_HASHES] + ["/"+FOURTH_PREFIX+i+".jpg" for i in FOURTH_HASHES]:
        raise RuntimeError("CHINA_ORDER: photo identity mismatch")
    for p in root.glob("*.html"):
        if p.name != PAGE and "/assets/china-order/" in p.read_text(encoding="utf-8"):
            raise RuntimeError("CHINA_ORDER: supplier photo outside dedicated section")
    return expected
