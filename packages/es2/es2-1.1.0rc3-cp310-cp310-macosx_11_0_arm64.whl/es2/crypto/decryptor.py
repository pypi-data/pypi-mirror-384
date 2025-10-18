# ========================================================================================
#  Copyright (C) 2025 CryptoLab Inc. All rights reserved.
#
#  This software is proprietary and confidential.
#  Unauthorized use, modification, reproduction, or redistribution is strictly prohibited.
#
#  Commercial use is permitted only under a separate, signed agreement with CryptoLab Inc.
#
#  For licensing inquiries or permission requests, please contact: pypi@cryptolab.co.kr
# ========================================================================================

from typing import Optional

import evi
from evi import SealInfo, SealMode

from es2.crypto.context import Context
from es2.crypto.parameter import ContextParameter

###################################
# Decryptor Class
###################################


class Decryptor:
    """
    Provides decryption functionality for encrypted vectors using the HEaaN homomorphic encryption library..
    Decryptor requires a context and either a file path to the secret key.

    Parameters
    ----------
    key_path : Optional[str]
        The file path to the secret key used for decryption. If not provided, it defaults to None.

    Example
    --------
    >>> dec = Decryptor()
    >>> decrypted_score = dec.decrypt_score(encrypted_score, sec_key_path="/path/to/SecKey.bin")
    """

    _context: Context = None

    def __init__(self, key_path: Optional[str] = None, seal_info: Optional[SealInfo] = SealInfo(SealMode.NONE)):
        if Decryptor._context is None:
            raise ValueError("Context must be initialized before creating a Decryptor instance.")
        if key_path is not None and key_path.endswith("SecKeyD16.bin"):
            if Decryptor._context.is_ip():
                raise ValueError("IP preset does not support SecKeyD16.bin")
            self._decryptor = evi.Decryptor(key_path)
        else:
            self._decryptor = evi.Decryptor(Decryptor._context._context)
        self._decryptor_type = Decryptor._context.search_type
        self._context_param = Decryptor._context.parameter
        self._seal_info = seal_info

    @classmethod
    def _create_from_context_parameter(
        cls,
        context_param: ContextParameter,
        key_path: Optional[str] = None,
        seal_info: Optional[SealInfo] = SealInfo(SealMode.NONE),
    ):
        """
        Creates a Decryptor instance from a ContextParameter object and an optional key path.

        Parameters
        ----------
        context_param : ContextParameter
            The ContextParameter object containing the preset, dimension, and device type.
        key_path : str
            The file path to the secret key used for decryption.

        Returns
        -------
        Decryptor
            A new Decryptor instance initialized with the provided ContextParameter and key path.
        """
        if cls._context is None or cls._context.parameter.dim != context_param.dim:
            cls._context = Context._create_from_parameter(context_param)
        return cls(key_path, seal_info=seal_info)

    @property
    def decryptor(self):
        """
        Returns the decryptor object.
        Returns:
            evi.Decryptor: The decryptor object for decryption operations.
        """
        return self._decryptor

    @property
    def decryptor_type(self):
        """
        Returns the type of decryptor.

        Returns:
            str: The type of decryptor, either "IP" or "QF".
        """
        return self._decryptor_type

    @property
    def context_param(self) -> ContextParameter:
        """
        Returns the ContextParameter object associated with this decryptor.

        Returns:
            ContextParameter: The parameter object for this decryptor.
        """
        return self._context_param

    @property
    def seal_info(self):
        return self._seal_info

    @seal_info.setter
    def seal_info(self, seal_info: Optional[SealInfo]):
        if seal_info is None:
            seal_info = SealInfo(SealMode.NONE)
        self._seal_info = seal_info

    @property
    def seal_mode_name(self):
        return self.seal_info.mode.name

    def decrypt(self, enc_msg, sec_key_path: str, is_score: bool = False):
        sec_key = evi.SecretKey(sec_key_path, self.seal_info)
        """
        Decrypts an encrypted vector.

        Parameters
        ----------
        enc_msg : evi.Quey
            The encrypted vector to decrypt.
        sec_key_path : str
            The file path to the secret key used for decryption.
        is_score : bool, optional
            If True, the decryption will return the score of the encrypted vector.

        Returns
        -------
        List[float]
            The decrypted vector as a list of floats.
        """
        if is_score:
            result = self.decryptor.decrypt(enc_msg, sec_key, is_score)
            return result
        result = self.decryptor.decrypt(enc_msg, sec_key)
        sliced_result = result[: self.context_param.dim]
        return sliced_result

    def decrypt_with_idx(self, enc_msg, dec_idx, sec_key_path: str):
        """
        Decrypts an encrypted vector with a specific index.

        Parameters
        ----------
        enc_msg : evi.Query
            The encrypted vector to decrypt.
        dec_idx : int
            The index of the vector to decrypt.
        sec_key_path : str
            The file path to the secret key used for decryption.

        Returns
        -------
        List[float]
            The decrypted vector as a list of floats.
        """
        sec_key = evi.SecretKey(sec_key_path, seal_info=self.seal_info)
        res = self.decryptor.decrypt(dec_idx, enc_msg, sec_key)
        sliced = res[: self.context_param.dim]
        del sec_key
        return sliced

    def decrypt_score(self, enc_msg, sec_key_path: str):
        """
        Decrypts an encrypted result score.

        Parameters
        ----------
        enc_msg : evi.Ciphertext
            The encrypted vector to decrypt.
        sec_key_path : str
            The file path to the secret key used for decryption.

        Returns
        -------
        List[float]
            The decrypted vectors of score as a list of floats.

        Example
        --------
        >>> decrypted_score = dec.decrypt_score(encrypted_score, sec_key_path="/path/to/SecKey.bin")
        """
        dec_target = evi.SearchResult.deserializeFrom(enc_msg.data)

        return self.decrypt(dec_target, sec_key_path=sec_key_path, is_score=True)[: dec_target.get_item_count()]

    # def get_cleaner(self):
    #     return self.decryptor.get_cleaner()

    # def get_context(self):
    #     return self.decryptor.get_context()
    #       => Not supported yet
