#ifndef DEB_DEB_H
#define DEB_DEB_H

#include "deb/deb_type.h"

#ifdef __cplusplus
extern "C" {
#endif

// ---------------------------------------------------------------------
// SecretKey management APIs
// ---------------------------------------------------------------------
DEB_API deb_status_t deb_generate_secretkey(const deb_preset_t preset,
                                         deb_sk_t *sk);

// ---------------------------------------------------------------------
// Encrypt/Decrypt APIs
// ---------------------------------------------------------------------

/**
 * deb_encrypt
 *
 * Encrypts a message using a secret key.
 * The message must be initialized and the secret key must be generated.
 * If the message is not initialized or the secret key is not generated,
 * the function will return an error.
 *
 * @param msg Pointer to the message to encrypt.
 * @param sk Pointer to the secret key to use for encryption.
 * @param cipher Pointer to the cipher to store the encrypted message.
 * @return DEB_STATUS_OK on success, or an error code on failure.
 **/
DEB_API deb_status_t deb_encrypt(const deb_message_t *msg, const deb_sk_t *sk,
                                 deb_cipher_t *cipher);
DEB_API deb_status_t deb_encrypt_with_enckey(const deb_message_t *msg,
                                             const deb_swk_t *enckey,
                                             deb_cipher_t *cipher);
DEB_API deb_status_t deb_encrypt_coeff(const deb_coeff_t *coeff,
                                       const deb_sk_t *sk,
                                       deb_cipher_t *cipher);
DEB_API deb_status_t deb_encrypt_coeff_with_enckey(const deb_coeff_t *coeff,
                                                   const deb_swk_t *enckey,
                                                   deb_cipher_t *cipher);

DEB_API deb_status_t deb_scale_encrypt(const deb_message_t *msg,
                                       const deb_sk_t *sk, deb_cipher_t *cipher,
                                       double scale);
DEB_API deb_status_t deb_scale_encrypt_with_enckey(const deb_message_t *msg,
                                                   const deb_swk_t *enckey,
                                                   deb_cipher_t *cipher,
                                                   double scale);
DEB_API deb_status_t deb_scale_encrypt_coeff(const deb_coeff_t *coeff,
                                             const deb_sk_t *sk,
                                             deb_cipher_t *cipher,
                                             double scale);
DEB_API deb_status_t deb_scale_encrypt_coeff_with_enckey(
    const deb_coeff_t *coeff, const deb_swk_t *enckey, deb_cipher_t *cipher,
    double scale);
/**
 * deb_decrypt
 *
 * Decrypts a cipher using a secret key.
 * The cipher must be initialized and the secret key must be generated.
 * If the cipher is not initialized or the secret key is not generated,
 * the function will return an error.
 *
 * @param cipher Pointer to the cipher to decrypt.
 * @param sk Pointer to the secret key to use for decryption.
 * @param msg Pointer to the message to store the decrypted result.
 * @return DEB_STATUS_OK on success, or an error code on failure.
 **/
DEB_API deb_status_t deb_decrypt(const deb_cipher_t *cipher, const deb_sk_t *sk,
                                 deb_message_t *msg);
DEB_API deb_status_t deb_decrypt_to_coeff(const deb_cipher_t *cipher,
                                          const deb_sk_t *sk,
                                          deb_coeff_t *coeff);
DEB_API deb_status_t deb_scale_decrypt(const deb_cipher_t *cipher,
                                       const deb_sk_t *sk, double scale,
                                       deb_message_t *msg);
DEB_API deb_status_t deb_scale_decrypt_to_coeff(const deb_cipher_t *cipher,
                                                const deb_sk_t *sk,
                                                double scale,
                                                deb_coeff_t *coeff);
// ---------------------------------------------------------------------
// Switching(Evaluation) key management APIs
// ---------------------------------------------------------------------

DEB_API deb_status_t deb_generate_secretkey_with_coeff(const deb_preset_t preset,
                                                 const int8_t *coeff,
                                                 deb_sk_t **sk);
DEB_API deb_status_t deb_generate_enckey(const deb_sk_t *sk, deb_swk_t *enckey);
DEB_API deb_status_t deb_generate_multkey(const deb_sk_t *sk, deb_swk_t *multkey);
DEB_API deb_status_t deb_generate_conjkey(const deb_sk_t *sk, deb_swk_t *conjkey);
DEB_API deb_status_t deb_generate_rotkey(const deb_sk_t *sk, const deb_size_t rot_idx,
                                        deb_swk_t *rotkey);
DEB_API deb_status_t deb_generate_modpackkey(const deb_sk_t *sk, deb_swk_t *modpackkey);


#ifdef __cplusplus
}
#endif
#endif // DEB_DEB_H
