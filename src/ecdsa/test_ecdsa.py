from __future__ import print_function
import sys
import hypothesis.strategies as st
from hypothesis import given, settings, note, example

try:
    import unittest2 as unittest
except ImportError:
    import unittest
import pytest
from .ecdsa import (
    Private_key,
    Public_key,
    Signature,
    generator_192,
    digest_integer,
    ellipticcurve,
    point_is_valid,
    generator_224,
    generator_256,
    generator_384,
    generator_521,
    generator_secp256k1,
    curve_192,
    InvalidPointError,
    curve_112r2,
    generator_112r2,
    int_to_string,
)


HYP_SETTINGS = {}
# old hypothesis doesn't have the "deadline" setting
if sys.version_info > (2, 7):  # pragma: no branch
    # SEC521p is slow, allow long execution for it
    HYP_SETTINGS["deadline"] = 5000


class TestP192FromX9_62(unittest.TestCase):
    """Check test vectors from X9.62"""

    @classmethod
    def setUpClass(cls):
        cls.d = 651056770906015076056810763456358567190100156695615665659
        cls.Q = cls.d * generator_192
        cls.k = 6140507067065001063065065565667405560006161556565665656654
        cls.R = cls.k * generator_192

        cls.msg = 968236873715988614170569073515315707566766479517
        cls.pubk = Public_key(generator_192, generator_192 * cls.d)
        cls.privk = Private_key(cls.pubk, cls.d)
        cls.sig = cls.privk.sign(cls.msg, cls.k)

    def test_point_multiplication(self):
        assert self.Q.x() == 0x62B12D60690CDCF330BABAB6E69763B471F994DD702D16A5

    def test_point_multiplication_2(self):
        assert self.R.x() == 0x885052380FF147B734C330C43D39B2C4A89F29B0F749FEAD
        assert self.R.y() == 0x9CF9FA1CBEFEFB917747A3BB29C072B9289C2547884FD835

    def test_mult_and_addition(self):
        u1 = 2563697409189434185194736134579731015366492496392189760599
        u2 = 6266643813348617967186477710235785849136406323338782220568
        temp = u1 * generator_192 + u2 * self.Q
        assert temp.x() == 0x885052380FF147B734C330C43D39B2C4A89F29B0F749FEAD
        assert temp.y() == 0x9CF9FA1CBEFEFB917747A3BB29C072B9289C2547884FD835

    def test_signature(self):
        r, s = self.sig.r, self.sig.s
        assert r == 3342403536405981729393488334694600415596881826869351677613
        assert s == 5735822328888155254683894997897571951568553642892029982342

    def test_verification(self):
        assert self.pubk.verifies(self.msg, self.sig)

    def test_rejection(self):
        assert not self.pubk.verifies(self.msg - 1, self.sig)


class TestPublicKey(unittest.TestCase):
    def test_equality_public_keys(self):
        gen = generator_192
        x = 0xC58D61F88D905293BCD4CD0080BCB1B7F811F2FFA41979F6
        y = 0x8804DC7A7C4C7F8B5D437F5156F3312CA7D6DE8A0E11867F
        point = ellipticcurve.Point(gen.curve(), x, y)
        pub_key1 = Public_key(gen, point)
        pub_key2 = Public_key(gen, point)
        self.assertEqual(pub_key1, pub_key2)

    def test_inequality_public_key(self):
        gen = generator_192
        x1 = 0xC58D61F88D905293BCD4CD0080BCB1B7F811F2FFA41979F6
        y1 = 0x8804DC7A7C4C7F8B5D437F5156F3312CA7D6DE8A0E11867F
        point1 = ellipticcurve.Point(gen.curve(), x1, y1)

        x2 = 0x6A223D00BD22C52833409A163E057E5B5DA1DEF2A197DD15
        y2 = 0x7B482604199367F1F303F9EF627F922F97023E90EAE08ABF
        point2 = ellipticcurve.Point(gen.curve(), x2, y2)

        pub_key1 = Public_key(gen, point1)
        pub_key2 = Public_key(gen, point2)
        self.assertNotEqual(pub_key1, pub_key2)

    def test_inequality_different_curves(self):
        gen = generator_192
        x1 = 0xC58D61F88D905293BCD4CD0080BCB1B7F811F2FFA41979F6
        y1 = 0x8804DC7A7C4C7F8B5D437F5156F3312CA7D6DE8A0E11867F
        point1 = ellipticcurve.Point(gen.curve(), x1, y1)

        x2 = 0x722BA0FB6B8FC8898A4C6AB49E66
        y2 = 0x2B7344BB57A7ABC8CA0F1A398C7D
        point2 = ellipticcurve.Point(generator_112r2.curve(), x2, y2)

        pub_key1 = Public_key(gen, point1)
        pub_key2 = Public_key(generator_112r2, point2)
        self.assertNotEqual(pub_key1, pub_key2)

    def test_inequality_public_key_not_implemented(self):
        gen = generator_192
        x = 0xC58D61F88D905293BCD4CD0080BCB1B7F811F2FFA41979F6
        y = 0x8804DC7A7C4C7F8B5D437F5156F3312CA7D6DE8A0E11867F
        point = ellipticcurve.Point(gen.curve(), x, y)
        pub_key = Public_key(gen, point)
        self.assertNotEqual(pub_key, None)

    def test_public_key_with_generator_without_order(self):
        gen = ellipticcurve.PointJacobi(
            generator_192.curve(), generator_192.x(), generator_192.y(), 1
        )

        x = 0xC58D61F88D905293BCD4CD0080BCB1B7F811F2FFA41979F6
        y = 0x8804DC7A7C4C7F8B5D437F5156F3312CA7D6DE8A0E11867F
        point = ellipticcurve.Point(gen.curve(), x, y)

        with self.assertRaises(InvalidPointError) as e:
            Public_key(gen, point)

        self.assertIn("Generator point must have order", str(e.exception))

    def test_public_point_on_curve_not_scalar_multiple_of_base_point(self):
        x = 2
        y = 0xBE6AA4938EF7CFE6FE29595B6B00
        # we need a curve with cofactor != 1
        point = ellipticcurve.PointJacobi(curve_112r2, x, y, 1)

        self.assertTrue(curve_112r2.contains_point(x, y))

        with self.assertRaises(InvalidPointError) as e:
            Public_key(generator_112r2, point)

        self.assertIn("Generator point order", str(e.exception))

    def test_point_is_valid_with_not_scalar_multiple_of_base_point(self):
        x = 2
        y = 0xBE6AA4938EF7CFE6FE29595B6B00

        self.assertFalse(point_is_valid(generator_112r2, x, y))

    # the tests to verify the extensiveness of tests in ecdsa.ecdsa
    # if PointJacobi gets modified to calculate the x and y mod p the tests
    # below will need to use a fake/mock object
    def test_invalid_point_x_negative(self):
        pt = ellipticcurve.PointJacobi(curve_192, -1, 0, 1)

        with self.assertRaises(InvalidPointError) as e:
            Public_key(generator_192, pt)

        self.assertIn("The public point has x or y", str(e.exception))

    def test_invalid_point_x_equal_p(self):
        pt = ellipticcurve.PointJacobi(curve_192, curve_192.p(), 0, 1)

        with self.assertRaises(InvalidPointError) as e:
            Public_key(generator_192, pt)

        self.assertIn("The public point has x or y", str(e.exception))

    def test_invalid_point_y_negative(self):
        pt = ellipticcurve.PointJacobi(curve_192, 0, -1, 1)

        with self.assertRaises(InvalidPointError) as e:
            Public_key(generator_192, pt)

        self.assertIn("The public point has x or y", str(e.exception))

    def test_invalid_point_y_equal_p(self):
        pt = ellipticcurve.PointJacobi(curve_192, 0, curve_192.p(), 1)

        with self.assertRaises(InvalidPointError) as e:
            Public_key(generator_192, pt)

        self.assertIn("The public point has x or y", str(e.exception))


class TestPublicKeyVerifies(unittest.TestCase):
    # test all the different ways that a signature can be publicly invalid
    @classmethod
    def setUpClass(cls):
        gen = generator_192
        x = 0xC58D61F88D905293BCD4CD0080BCB1B7F811F2FFA41979F6
        y = 0x8804DC7A7C4C7F8B5D437F5156F3312CA7D6DE8A0E11867F
        point = ellipticcurve.Point(gen.curve(), x, y)

        cls.pub_key = Public_key(gen, point)

    def test_sig_with_r_zero(self):
        sig = Signature(0, 1)

        self.assertFalse(self.pub_key.verifies(1, sig))

    def test_sig_with_r_order(self):
        sig = Signature(generator_192.order(), 1)

        self.assertFalse(self.pub_key.verifies(1, sig))

    def test_sig_with_s_zero(self):
        sig = Signature(1, 0)

        self.assertFalse(self.pub_key.verifies(1, sig))

    def test_sig_with_s_order(self):
        sig = Signature(1, generator_192.order())

        self.assertFalse(self.pub_key.verifies(1, sig))


class TestPrivateKey(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        gen = generator_192
        x = 0xC58D61F88D905293BCD4CD0080BCB1B7F811F2FFA41979F6
        y = 0x8804DC7A7C4C7F8B5D437F5156F3312CA7D6DE8A0E11867F
        point = ellipticcurve.Point(gen.curve(), x, y)
        cls.pub_key = Public_key(gen, point)

    def test_equality_private_keys(self):
        pr_key1 = Private_key(self.pub_key, 100)
        pr_key2 = Private_key(self.pub_key, 100)
        self.assertEqual(pr_key1, pr_key2)

    def test_inequality_private_keys(self):
        pr_key1 = Private_key(self.pub_key, 100)
        pr_key2 = Private_key(self.pub_key, 200)
        self.assertNotEqual(pr_key1, pr_key2)

    def test_inequality_private_keys_not_implemented(self):
        pr_key = Private_key(self.pub_key, 100)
        self.assertNotEqual(pr_key, None)


# Testing point validity, as per ECDSAVS.pdf B.2.2:
P192_POINTS = [
    (
        generator_192,
        0xCD6D0F029A023E9AACA429615B8F577ABEE685D8257CC83A,
        0x00019C410987680E9FB6C0B6ECC01D9A2647C8BAE27721BACDFC,
        False,
    ),
    (
        generator_192,
        0x00017F2FCE203639E9EAF9FB50B81FC32776B30E3B02AF16C73B,
        0x95DA95C5E72DD48E229D4748D4EEE658A9A54111B23B2ADB,
        False,
    ),
    (
        generator_192,
        0x4F77F8BC7FCCBADD5760F4938746D5F253EE2168C1CF2792,
        0x000147156FF824D131629739817EDB197717C41AAB5C2A70F0F6,
        False,
    ),
    (
        generator_192,
        0xC58D61F88D905293BCD4CD0080BCB1B7F811F2FFA41979F6,
        0x8804DC7A7C4C7F8B5D437F5156F3312CA7D6DE8A0E11867F,
        True,
    ),
    (
        generator_192,
        0xCDF56C1AA3D8AFC53C521ADF3FFB96734A6A630A4A5B5A70,
        0x97C1C44A5FB229007B5EC5D25F7413D170068FFD023CAA4E,
        True,
    ),
    (
        generator_192,
        0x89009C0DC361C81E99280C8E91DF578DF88CDF4B0CDEDCED,
        0x27BE44A529B7513E727251F128B34262A0FD4D8EC82377B9,
        True,
    ),
    (
        generator_192,
        0x6A223D00BD22C52833409A163E057E5B5DA1DEF2A197DD15,
        0x7B482604199367F1F303F9EF627F922F97023E90EAE08ABF,
        True,
    ),
    (
        generator_192,
        0x6DCCBDE75C0948C98DAB32EA0BC59FE125CF0FB1A3798EDA,
        0x0001171A3E0FA60CF3096F4E116B556198DE430E1FBD330C8835,
        False,
    ),
    (
        generator_192,
        0xD266B39E1F491FC4ACBBBC7D098430931CFA66D55015AF12,
        0x193782EB909E391A3148B7764E6B234AA94E48D30A16DBB2,
        False,
    ),
    (
        generator_192,
        0x9D6DDBCD439BAA0C6B80A654091680E462A7D1D3F1FFEB43,
        0x6AD8EFC4D133CCF167C44EB4691C80ABFFB9F82B932B8CAA,
        False,
    ),
    (
        generator_192,
        0x146479D944E6BDA87E5B35818AA666A4C998A71F4E95EDBC,
        0xA86D6FE62BC8FBD88139693F842635F687F132255858E7F6,
        False,
    ),
    (
        generator_192,
        0xE594D4A598046F3598243F50FD2C7BD7D380EDB055802253,
        0x509014C0C4D6B536E3CA750EC09066AF39B4C8616A53A923,
        False,
    ),
]


@pytest.mark.parametrize("generator,x,y,expected", P192_POINTS)
def test_point_validity(generator, x, y, expected):
    """
    `generator` defines the curve; is `(x, y)` a point on
    this curve? `expected` is True if the right answer is Yes.
    """
    assert point_is_valid(generator, x, y) == expected


# Trying signature-verification tests from ECDSAVS.pdf B.2.4:
CURVE_192_KATS = [
    (
        generator_192,
        int(
            "0x84ce72aa8699df436059f052ac51b6398d2511e49631bcb7e71f89c499b9ee"
            "425dfbc13a5f6d408471b054f2655617cbbaf7937b7c80cd8865cf02c8487d30"
            "d2b0fbd8b2c4e102e16d828374bbc47b93852f212d5043c3ea720f086178ff79"
            "8cc4f63f787b9c2e419efa033e7644ea7936f54462dc21a6c4580725f7f0e7d1"
            "58",
            16,
        ),
        0xD9DBFB332AA8E5FF091E8CE535857C37C73F6250FFB2E7AC,
        0x282102E364FEDED3AD15DDF968F88D8321AA268DD483EBC4,
        0x64DCA58A20787C488D11D6DD96313F1B766F2D8EFE122916,
        0x1ECBA28141E84AB4ECAD92F56720E2CC83EB3D22DEC72479,
        True,
    ),
    (
        generator_192,
        int(
            "0x94bb5bacd5f8ea765810024db87f4224ad71362a3c28284b2b9f39fab86db1"
            "2e8beb94aae899768229be8fdb6c4f12f28912bb604703a79ccff769c1607f5a"
            "91450f30ba0460d359d9126cbd6296be6d9c4bb96c0ee74cbb44197c207f6db3"
            "26ab6f5a659113a9034e54be7b041ced9dcf6458d7fb9cbfb2744d999f7dfd63"
            "f4",
            16,
        ),
        0x3E53EF8D3112AF3285C0E74842090712CD324832D4277AE7,
        0xCC75F8952D30AEC2CBB719FC6AA9934590B5D0FF5A83ADB7,
        0x8285261607283BA18F335026130BAB31840DCFD9C3E555AF,
        0x356D89E1B04541AFC9704A45E9C535CE4A50929E33D7E06C,
        True,
    ),
    (
        generator_192,
        int(
            "0xf6227a8eeb34afed1621dcc89a91d72ea212cb2f476839d9b4243c66877911"
            "b37b4ad6f4448792a7bbba76c63bdd63414b6facab7dc71c3396a73bd7ee14cd"
            "d41a659c61c99b779cecf07bc51ab391aa3252386242b9853ea7da67fd768d30"
            "3f1b9b513d401565b6f1eb722dfdb96b519fe4f9bd5de67ae131e64b40e78c42"
            "dd",
            16,
        ),
        0x16335DBE95F8E8254A4E04575D736BEFB258B8657F773CB7,
        0x421B13379C59BC9DCE38A1099CA79BBD06D647C7F6242336,
        0x4141BD5D64EA36C5B0BD21EF28C02DA216ED9D04522B1E91,
        0x159A6AA852BCC579E821B7BB0994C0861FB08280C38DAA09,
        False,
    ),
    (
        generator_192,
        int(
            "0x16b5f93afd0d02246f662761ed8e0dd9504681ed02a253006eb36736b56309"
            "7ba39f81c8e1bce7a16c1339e345efabbc6baa3efb0612948ae51103382a8ee8"
            "bc448e3ef71e9f6f7a9676694831d7f5dd0db5446f179bcb737d4a526367a447"
            "bfe2c857521c7f40b6d7d7e01a180d92431fb0bbd29c04a0c420a57b3ed26ccd"
            "8a",
            16,
        ),
        0xFD14CDF1607F5EFB7B1793037B15BDF4BAA6F7C16341AB0B,
        0x83FA0795CC6C4795B9016DAC928FD6BAC32F3229A96312C4,
        0x8DFDB832951E0167C5D762A473C0416C5C15BC1195667DC1,
        0x1720288A2DC13FA1EC78F763F8FE2FF7354A7E6FDDE44520,
        False,
    ),
    (
        generator_192,
        int(
            "0x08a2024b61b79d260e3bb43ef15659aec89e5b560199bc82cf7c65c77d3919"
            "2e03b9a895d766655105edd9188242b91fbde4167f7862d4ddd61e5d4ab55196"
            "683d4f13ceb90d87aea6e07eb50a874e33086c4a7cb0273a8e1c4408f4b846bc"
            "eae1ebaac1b2b2ea851a9b09de322efe34cebe601653efd6ddc876ce8c2f2072"
            "fb",
            16,
        ),
        0x674F941DC1A1F8B763C9334D726172D527B90CA324DB8828,
        0x65ADFA32E8B236CB33A3E84CF59BFB9417AE7E8EDE57A7FF,
        0x9508B9FDD7DAF0D8126F9E2BC5A35E4C6D800B5B804D7796,
        0x36F2BF6B21B987C77B53BB801B3435A577E3D493744BFAB0,
        False,
    ),
    (
        generator_192,
        int(
            "0x1843aba74b0789d4ac6b0b8923848023a644a7b70afa23b1191829bbe4397c"
            "e15b629bf21a8838298653ed0c19222b95fa4f7390d1b4c844d96e645537e0aa"
            "e98afb5c0ac3bd0e4c37f8daaff25556c64e98c319c52687c904c4de7240a1cc"
            "55cd9756b7edaef184e6e23b385726e9ffcba8001b8f574987c1a3fedaaa83ca"
            "6d",
            16,
        ),
        0x10ECCA1AAD7220B56A62008B35170BFD5E35885C4014A19F,
        0x04EB61984C6C12ADE3BC47F3C629ECE7AA0A033B9948D686,
        0x82BFA4E82C0DFE9274169B86694E76CE993FD83B5C60F325,
        0xA97685676C59A65DBDE002FE9D613431FB183E8006D05633,
        False,
    ),
    (
        generator_192,
        int(
            "0x5a478f4084ddd1a7fea038aa9732a822106385797d02311aeef4d0264f824f"
            "698df7a48cfb6b578cf3da416bc0799425bb491be5b5ecc37995b85b03420a98"
            "f2c4dc5c31a69a379e9e322fbe706bbcaf0f77175e05cbb4fa162e0da82010a2"
            "78461e3e974d137bc746d1880d6eb02aa95216014b37480d84b87f717bb13f76"
            "e1",
            16,
        ),
        0x6636653CB5B894CA65C448277B29DA3AD101C4C2300F7C04,
        0xFDF1CBB3FC3FD6A4F890B59E554544175FA77DBDBEB656C1,
        0xEAC2DDECDDFB79931A9C3D49C08DE0645C783A24CB365E1C,
        0x3549FEE3CFA7E5F93BC47D92D8BA100E881A2A93C22F8D50,
        False,
    ),
    (
        generator_192,
        int(
            "0xc598774259a058fa65212ac57eaa4f52240e629ef4c310722088292d1d4af6"
            "c39b49ce06ba77e4247b20637174d0bd67c9723feb57b5ead232b47ea452d5d7"
            "a089f17c00b8b6767e434a5e16c231ba0efa718a340bf41d67ea2d295812ff1b"
            "9277daacb8bc27b50ea5e6443bcf95ef4e9f5468fe78485236313d53d1c68f6b"
            "a2",
            16,
        ),
        0xA82BD718D01D354001148CD5F69B9EBF38FF6F21898F8AAA,
        0xE67CEEDE07FC2EBFAFD62462A51E4B6C6B3D5B537B7CAF3E,
        0x4D292486C620C3DE20856E57D3BB72FCDE4A73AD26376955,
        0xA85289591A6081D5728825520E62FF1C64F94235C04C7F95,
        False,
    ),
    (
        generator_192,
        int(
            "0xca98ed9db081a07b7557f24ced6c7b9891269a95d2026747add9e9eb80638a"
            "961cf9c71a1b9f2c29744180bd4c3d3db60f2243c5c0b7cc8a8d40a3f9a7fc91"
            "0250f2187136ee6413ffc67f1a25e1c4c204fa9635312252ac0e0481d89b6d53"
            "808f0c496ba87631803f6c572c1f61fa049737fdacce4adff757afed4f05beb6"
            "58",
            16,
        ),
        0x7D3B016B57758B160C4FCA73D48DF07AE3B6B30225126C2F,
        0x4AF3790D9775742BDE46F8DA876711BE1B65244B2B39E7EC,
        0x95F778F5F656511A5AB49A5D69DDD0929563C29CBC3A9E62,
        0x75C87FC358C251B4C83D2DD979FAAD496B539F9F2EE7A289,
        False,
    ),
    (
        generator_192,
        int(
            "0x31dd9a54c8338bea06b87eca813d555ad1850fac9742ef0bbe40dad400e102"
            "88acc9c11ea7dac79eb16378ebea9490e09536099f1b993e2653cd50240014c9"
            "0a9c987f64545abc6a536b9bd2435eb5e911fdfde2f13be96ea36ad38df4ae9e"
            "a387b29cced599af777338af2794820c9cce43b51d2112380a35802ab7e396c9"
            "7a",
            16,
        ),
        0x9362F28C4EF96453D8A2F849F21E881CD7566887DA8BEB4A,
        0xE64D26D8D74C48A024AE85D982EE74CD16046F4EE5333905,
        0xF3923476A296C88287E8DE914B0B324AD5A963319A4FE73B,
        0xF0BAEED7624ED00D15244D8BA2AEDE085517DBDEC8AC65F5,
        True,
    ),
    (
        generator_192,
        int(
            "0xb2b94e4432267c92f9fdb9dc6040c95ffa477652761290d3c7de312283f645"
            "0d89cc4aabe748554dfb6056b2d8e99c7aeaad9cdddebdee9dbc099839562d90"
            "64e68e7bb5f3a6bba0749ca9a538181fc785553a4000785d73cc207922f63e8c"
            "e1112768cb1de7b673aed83a1e4a74592f1268d8e2a4e9e63d414b5d442bd045"
            "6d",
            16,
        ),
        0xCC6FC032A846AAAC25533EB033522824F94E670FA997ECEF,
        0xE25463EF77A029ECCDA8B294FD63DD694E38D223D30862F1,
        0x066B1D07F3A40E679B620EDA7F550842A35C18B80C5EBE06,
        0xA0B0FB201E8F2DF65E2C4508EF303BDC90D934016F16B2DC,
        False,
    ),
    (
        generator_192,
        int(
            "0x4366fcadf10d30d086911de30143da6f579527036937007b337f7282460eae"
            "5678b15cccda853193ea5fc4bc0a6b9d7a31128f27e1214988592827520b214e"
            "ed5052f7775b750b0c6b15f145453ba3fee24a085d65287e10509eb5d5f602c4"
            "40341376b95c24e5c4727d4b859bfe1483d20538acdd92c7997fa9c614f0f839"
            "d7",
            16,
        ),
        0x955C908FE900A996F7E2089BEE2F6376830F76A19135E753,
        0xBA0C42A91D3847DE4A592A46DC3FDAF45A7CC709B90DE520,
        0x1F58AD77FC04C782815A1405B0925E72095D906CBF52A668,
        0xF2E93758B3AF75EDF784F05A6761C9B9A6043C66B845B599,
        False,
    ),
    (
        generator_192,
        int(
            "0x543f8af57d750e33aa8565e0cae92bfa7a1ff78833093421c2942cadf99866"
            "70a5ff3244c02a8225e790fbf30ea84c74720abf99cfd10d02d34377c3d3b412"
            "69bea763384f372bb786b5846f58932defa68023136cd571863b304886e95e52"
            "e7877f445b9364b3f06f3c28da12707673fecb4b8071de06b6e0a3c87da160ce"
            "f3",
            16,
        ),
        0x31F7FA05576D78A949B24812D4383107A9A45BB5FCCDD835,
        0x8DC0EB65994A90F02B5E19BD18B32D61150746C09107E76B,
        0xBE26D59E4E883DDE7C286614A767B31E49AD88789D3A78FF,
        0x8762CA831C1CE42DF77893C9B03119428E7A9B819B619068,
        False,
    ),
    (
        generator_192,
        int(
            "0xd2e8454143ce281e609a9d748014dcebb9d0bc53adb02443a6aac2ffe6cb009f"
            "387c346ecb051791404f79e902ee333ad65e5c8cb38dc0d1d39a8dc90add502357"
            "2720e5b94b190d43dd0d7873397504c0c7aef2727e628eb6a74411f2e400c65670"
            "716cb4a815dc91cbbfeb7cfe8c929e93184c938af2c078584da045e8f8d1",
            16,
        ),
        0x66AA8EDBBDB5CF8E28CEB51B5BDA891CAE2DF84819FE25C0,
        0x0C6BC2F69030A7CE58D4A00E3B3349844784A13B8936F8DA,
        0xA4661E69B1734F4A71B788410A464B71E7FFE42334484F23,
        0x738421CF5E049159D69C57A915143E226CAC8355E149AFE9,
        False,
    ),
    (
        generator_192,
        int(
            "0x6660717144040f3e2f95a4e25b08a7079c702a8b29babad5a19a87654bc5c5af"
            "a261512a11b998a4fb36b5d8fe8bd942792ff0324b108120de86d63f65855e5461"
            "184fc96a0a8ffd2ce6d5dfb0230cbbdd98f8543e361b3205f5da3d500fdc8bac6d"
            "b377d75ebef3cb8f4d1ff738071ad0938917889250b41dd1d98896ca06fb",
            16,
        ),
        0xBCFACF45139B6F5F690A4C35A5FFFA498794136A2353FC77,
        0x6F4A6C906316A6AFC6D98FE1F0399D056F128FE0270B0F22,
        0x9DB679A3DAFE48F7CCAD122933ACFE9DA0970B71C94C21C1,
        0x984C2DB99827576C0A41A5DA41E07D8CC768BC82F18C9DA9,
        False,
    ),
]


@pytest.mark.parametrize("gen,msg,qx,qy,r,s,expected", CURVE_192_KATS)
def test_signature_validity(gen, msg, qx, qy, r, s, expected):
    """
    `msg` = message, `qx` and `qy` represent the base point on
    elliptic curve of `gen`, `r` and `s` are the signature, and
    `expected` is True iff the signature is expected to be valid."""
    pubk = Public_key(gen, ellipticcurve.Point(gen.curve(), qx, qy))
    assert expected == pubk.verifies(digest_integer(msg), Signature(r, s))


@pytest.mark.parametrize(
    "gen,msg,qx,qy,r,s,expected", [x for x in CURVE_192_KATS if x[6]]
)
def test_pk_recovery(gen, msg, r, s, qx, qy, expected):
    del expected
    sign = Signature(r, s)
    pks = sign.recover_public_keys(digest_integer(msg), gen)

    assert pks

    # Test if the signature is valid for all found public keys
    for pk in pks:
        q = pk.point
        test_signature_validity(gen, msg, q.x(), q.y(), r, s, True)

    # Test if the original public key is in the set of found keys
    original_q = ellipticcurve.Point(gen.curve(), qx, qy)
    points = [pk.point for pk in pks]
    assert original_q in points


@st.composite
def st_random_gen_key_msg_nonce(draw):
    """Hypothesis strategy for test_sig_verify()."""
    name_gen = {
        "generator_192": generator_192,
        "generator_224": generator_224,
        "generator_256": generator_256,
        "generator_secp256k1": generator_secp256k1,
        "generator_384": generator_384,
        "generator_521": generator_521,
    }
    name = draw(st.sampled_from(sorted(name_gen.keys())))
    note("Generator used: {0}".format(name))
    generator = name_gen[name]
    order = int(generator.order()) - 1

    key = draw(st.integers(min_value=1, max_value=order))
    msg = draw(st.integers(min_value=1, max_value=order))
    nonce = draw(
        st.integers(min_value=1, max_value=order)
        | st.integers(min_value=order >> 1, max_value=order)
    )
    return generator, key, msg, nonce


SIG_VER_SETTINGS = dict(HYP_SETTINGS)
if "--fast" in sys.argv:
    SIG_VER_SETTINGS["max_examples"] = 1
else:
    SIG_VER_SETTINGS["max_examples"] = 10


@settings(**SIG_VER_SETTINGS)
@example((generator_224, 4, 1, 1))
@given(st_random_gen_key_msg_nonce())
def test_sig_verify(args):
    """
    Check if signing and verification works for arbitrary messages and
    that signatures for other messages are rejected.
    """
    generator, sec_mult, msg, nonce = args

    pubkey = Public_key(generator, generator * sec_mult)
    privkey = Private_key(pubkey, sec_mult)

    signature = privkey.sign(msg, nonce)

    assert pubkey.verifies(msg, signature)

    assert not pubkey.verifies(msg - 1, signature)


def test_int_to_string_with_zero():
    assert int_to_string(0) == b"\x00"
