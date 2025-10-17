"""
List of "shitcoins" (but like, actual shit shitcoins) to ignore in all
Yearn Treasury analytics.

This module defines, for each blockchain network, a set of token addresses
known to be unpricable, considered as spam, or otherwise unwanted for
reporting and analytics. These tokens are passed in to :mod:`eth-portfolio`,
which contains the logic that prevents these shitcoins from being included in
any Yearn Treasury outputs.

Since these tokens do nothing but add noise to the outputs, transactions
involving them are excluded from treasury calculations, reports, and dashboards.
"""

from typing import Final

from y import Network, convert
from y.constants import CHAINID


_SHITCOINS: Final = {
    Network.Mainnet: (
        "0xC36442b4a4522E871399CD717aBDD847Ab11FE88",  # UNI-V3 NFT, not shitcoin but not pricable
        "0x0329b631464C43f4e8132df7B4ac29a2D89FFdC7",
        "0xa191021599f60E2fDE1bc8c8d1a07e9BD663c4a9",
        "0xD1E5b0FF1287aA9f9A268759062E4Ab08b9Dacbe",  # .crypto domain NFT
        "0x0B39Bb088f03b0baeA1AAC64AaEAb85E714c76e2",
        "0x6cC759B8cE30e719511B6a897CfE449A19f64a92",
        "0xD7aBCFd05a9ba3ACbc164624402fB2E95eC41be6",
        "0xeaaa790591c646b0436f02f63e8Ca56209FEDE4E",
        "0x1e988ba4692e52Bc50b375bcC8585b95c48AaD77",
        "0xeF81c2C98cb9718003A89908e6bd1a5fA8A098A3",
        "0x174Cd3359C6a4E6B64D2995Da4E2E4631379526E",
        "0x1d41cf24dF81E3134319BC11c308c5589A486166",
        "0x437a6B880d4b3Be9ed93BD66D6B7f872fc0f5b5E",
        "0x53fFFB19BAcD44b82e204d036D579E86097E5D09",
        "0x9694EED198C1b7aB81ADdaf36255Ea58acf13Fab",
        "0x1AbBaC88B8F47D46a3d822eFA75F64A15C25966f",
        "0x195EC13Ef52c30CEb4019A055e7938DAfAE21B6a",
        "0xde32436e18c6946ED3559B925e3340Bf6D80B67A",
        "0x2Fe158f89F32C9C5E6C7082487DBB26e42071512",
        "0x9017201ae20f0940dB37723Cd704e80BcaA1347c",
        "0x5C3509b1BeB81aC9621AEd482a77038Ef1fD1f5D",
        "0x34D0f1Cb08D47dC1333657A0A84Df2462e806656",
        "0x799dc7a6017BC623A4fef6828FA49b5661ed53fb",
        "0xA00C7A61BcBb3F0ABCafACD149A3008A153b2DAb",
        "0x11068577AE36897fFaB0024F010247B9129459E6",
        "0x57b9d10157f66D8C00a815B5E289a152DeDBE7ed",
        "0x01234567bac6fF94d7E4f0EE23119CF848F93245",
        "0xe5868468Cb6Dd5d6D7056bd93f084816c6eF075f",
        "0x0a24Bb4842c301276c65086B5d78D5C872993c72",
        "0x63125c0d5Cd9071de9A1ac84c400982f41C697AE",
        "0x4d22921215cF37e8d49e2Ac6d1F5e9672f63A7c6",
        "0xe2549E429B78458fa60BC7B1b284d4411E1D5105",
        "0xCfdD747d041397bcE08B0Fe6ebF7Ef65E9F46795",
        "0x9745969171a38B40db05c506fe2DA2C36f317627",
        "0x6051C1354Ccc51b4d561e43b02735DEaE64768B8",
        "0xf0814d0E47F2390a8082C4a1BD819FDDe50f9bFc",
        "0x2DBd330bC9B7f3A822a9173aB52172BdDDcAcE2A",
        # just andre tinkering
        "0x5cB5e2d7Ab9Fd32021dF8F1D3E5269bD437Ec3Bf",
        # these arent shitcoins per se but we can't price them and dont expect to in the future, lets save cpu cycles
        "0x9d45DAb69f1309F1F55A7280b1f6a2699ec918E8",  # yFamily NFT <3
        "0x57f1887a8BF19b14fC0dF6Fd9B2acc9Af147eA85",  # ENS
        "0xD057B63f5E69CF1B929b356b579Cba08D7688048",  # vCOW
        "0x4c1317326fD8EFDeBdBE5e1cd052010D97723bd6",  # deprecated yCRV
        "0x8a0889d47f9Aa0Fac1cC718ba34E26b867437880",  # deprecated st-yCRV
        "0x55a290f08Bb4CAe8DcF1Ea5635A3FCfd4Da60456",  # BITTO
        "0x4770F3186225b1A6879983BD88C669CA55463886",  # 69XMins
        "0x05bAdF8A8e7fE5b43fae112108E26f2f663Bf1a2",  # INUNOMICS
        "0x3EF9181c9b96BAAafb3717A553E808Ccc72be37D",  # MEMEPEPE
        "0x5D22c8b4E3c90ca633e1377e6ca280a395fc61C0",  # XMEME
        "0x57f19E7e1A9066a741f59484481C4D2E9150e9E2",  # MOCO
        "0xb092D8E13Ba50963D57bEcB17a037728D883D02d",  # BABYLABUBU
        "0x4E51960bd33A6edA71a8B24A76311834BD98DD9f",  # AICC
        "0xB85485421d8a41C4648AB80bE1A725fA6b5Bc86d",  # MEGA
        "0x46D0Fb47b1e91130D53498EbeE7A968e7e6599f9",  # Ghibli
        "0x4FbB350052Bca5417566f188eB2EBCE5b19BC964",  # GRG
        "0x1f6DEb07E1a19bAfF90EC4075447eeF6eb96c0BA",  # BABYMANYU
        "0xD10EFABA11A51237fa120b15153DD432958bbDE3",  # JIFFPOM
        "0xCd9594cd25ED2a166362b6F76c523da08c4Ef2e5",  # ESTHER
        "0x16B907b5d1208Ae6086dE983a5EF45E7890eF272",  # JUNFOX
        "0xdE56173463d6461001B0891bC90DB224965f5762",  # MAGNUS
        "0x922824A5b3B3D5f4485fF52F4Ab7Cba5eA491874",  # POSEIDON
        "0x84F7D2f6FB447Bb11d3E7Ce64D83e1c02c2F3078",  # VIRTUAL
        # test token?
        "0x372d5d02c6b4075bd58892f80300cA590e92d29E",  # tOUSG
        # dETH? don't think this is needed
        "0x3d1E5Cf16077F349e999d6b21A4f646e83Cd90c5",
        # ai shitcoin spam
        "0xaf80B7dbeBbb5d9a4d33C453FcbF3d054DA53b25",  # NODEPAY AI
        "0xf960AbF9ccC883970BEa3E79f65027E27278e1A5",  # ASK AI
        "0xc136Eb8Abc892723aE87F355d12Cb721C4324D54",  # Grok3
        "0xc68bCEE3604F163f183Cf8B9a26E610E5961b037",  # TESLA AI
        "0xa65D56f8e074E773142205cD065FD0796B9aa483",  # MASSIVE AI
        "0x4e6c80aa486aF0ba20943Fbc067a5557DBcf5458",  # SUNO AI
        "0xC91223F844772dCdc2c6394585C8c30B3c1BE5C0",  # SEND AI
        "0x64b3336D1aDC6D3579e356760F53D3b018Cb11Bc",  # ALC AI
        "0x1495Ac869433698cCD2946c1e62D37bA766294A9",  # NVIDIA AI PC
        "0x8c0DF275c38092cd90Ae4d6147d8e619B3A24637",  # COLLE AI
        "0xe38f71fc2Ca5f5761cE21F39Fff2cE70662FA54c",  # CHAINOPERA AI
        "0xD2F89F59fBC7125b406e3F60A992DFa9FdB76524",  # MISTRAL AI
        "0xa0CCdBCeB5Da30F9d62F7A727F2B35C69dF08760",  # CHUNK AI
        "0x7CE31075d7450Aff4A9a82DdDF69D451B1e0C4E9",  # DEEPSEEK AI
        "0xf0f9C021AF9B6431FA59DAB75C8e6cB80c0dEa37",  # TESLA AI
        "0x635eeC65a7Ef10dCF96Bfe051D8A6e5960efe180",  # KLING AI
        "0xa3Efa0929569c15c20f89B591931899Fb05B4663",  # GPT-5
        "0x0A953979fdCfD82B08C77dB29705327BeC39ff13",  # GROK4 AI
        "0xc83377b9eE3CEe4Cc03CCd58AfdE1FB12864aEE3",  # E AI
        "0x927402ab67c0CDA3c187E9DFE34554AC581441f2",  # SAITABIT
        "0x691539810DF6e879A377C24CfEE130BBE92708d8",  # NVIDIA AI
        # matt furry spam
        "0x73228b3D33cC71cB721Fc62950577bE63bd9c8C9",  # Maskman by Matt Furie
        "0x7c28e66436C93BB9F657dDF2BA0eeeCf61369b92",  # Bloodboy by Matt Furie
        "0x70c5e1124569f17B1Be71E15833EaF1331f8727F",  # Pac-hat by Matt Furie
        "0xBd6555eC87C8A9a2280dCD6df45b9b074fC93Df2",  # Bork by Matt Furie
        # test token
        "0x2F375Ce83EE85e505150d24E85A1742fd03cA593",  # TEST
    ),
}
"""
Mapping of blockchain networks to tuples of token addresses that should be
ignored in Yearn Treasury analytics. These tokens are considered unpricable,
spam, or otherwise unwanted for reporting and analytics purposes.

Each tuple contains token contract addresses that will be excluded from
treasury calculations, reports, and dashboards for the corresponding network.
"""


SHITCOINS: Final = {convert.to_address(shitcoin) for shitcoin in _SHITCOINS.get(CHAINID, ())}  # type: ignore [call-overload]
"""Set of checksummed token addresses to ignore for the current chain.

This set is derived from the _SHITCOINS mapping for the current CHAINID,
and is used to filter out unpricable, spam, or otherwise unwanted tokens
from all Yearn Treasury analytics and reporting.
"""
