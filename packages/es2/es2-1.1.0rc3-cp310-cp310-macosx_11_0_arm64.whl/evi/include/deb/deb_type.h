#ifndef DEB_DEBTYPE_H
#define DEB_DEBTYPE_H

#include <stdbool.h>
#include <stddef.h>
#include <stdint.h>

#if defined(_WIN32) || defined(__CYGWIN__)
#define DEB_API __declspec(dllexport)
#else
#define DEB_API __attribute__((visibility("default")))
#endif

#ifdef __cplusplus
extern "C" {
#endif

//typedef int32_t deb_i32;
//typedef int64_t deb_i64;
//typedef uint32_t deb_u32;
typedef uint64_t deb_u64_t;
typedef uint32_t deb_size_t;
typedef double deb_real_t;

typedef enum {
    DEB_PRESET_FGb,
    DEB_PRESET_EVI_IP0,
    DEB_PRESET_EVI_QF,
    DEB_PRESET_FGbMS,
    DEB_PRESET_MAX, // This should be the last preset
} deb_preset_t;

typedef enum {
    DEB_STATUS_OK,
    DEB_STATUS_ERROR,
    DEB_STATUS_ALLOC_FAIL,
    DEB_STATUS_DEALLOC_FAIL,
    //DEB_STATUS_PRESET_ALREADY_LOADED,
    //DEB_STATUS_PRESET_NOT_LOADED,
    DEB_STATUS_INVALID_PRESET,
    DEB_STATUS_INVALID_SIZE,
    //DEB_STATUS_INVALID_CONTEXT,
    DEB_STATUS_NULL_POINTER_ERROR,
    DEB_STATUS_NOT_IMPLEMENTED,
} deb_status_t;

typedef enum {
    DEB_ENCODING_UNKNOWN,
    DEB_ENCODING_COEFF,
    DEB_ENCODING_SLOT,
    DEB_ENCODING_SWK,
} deb_encoding_t;

typedef enum {
    DEB_SWK_TYPE_GENERIC,
    DEB_SWK_TYPE_ENC,
    DEB_SWK_TYPE_MULT,
    DEB_SWK_TYPE_ROT,
    DEB_SWK_TYPE_CONJ,
    DEB_SWK_TYPE_RELIN,
    DEB_SWK_TYPE_AUTO,
    DEB_SWK_TYPE_MODPACK,
    DEB_SWK_TYPE_MODPACK_EVI,
    DEB_SWK_TYPE_MS_MODPACK_EVI,
    DEB_SWK_TYPE_MS_CC_MODPACK_EVI,
    DEB_SWK_TYPE_MS_SW_EVI,
    DEB_SWK_TYPE_MS_REVSW_EVI,
    DEB_SWK_TYPE_MS_ADDSW_EVI,
} deb_swk_kind_t;


// ---------------------------------------------------------------------
// Resource management APIs
// ---------------------------------------------------------------------

typedef struct deb_complex_t deb_complex_t;
DEB_API deb_status_t deb_create_complex(deb_real_t r, deb_real_t i, deb_complex_t **complex);
DEB_API deb_status_t deb_create_complex_zero(deb_complex_t **complex);
DEB_API deb_status_t deb_destroy_complex(deb_complex_t **complex);

typedef struct deb_message_t deb_message_t;
DEB_API deb_status_t deb_create_message_with_preset(const deb_preset_t preset, deb_message_t **msg);
DEB_API deb_status_t deb_create_message_with_size(const deb_size_t size, deb_message_t **msg);
DEB_API deb_status_t deb_create_message_with_init(const deb_size_t size, const deb_real_t r, const deb_real_t i, deb_message_t **msg);
DEB_API deb_status_t deb_destroy_message(deb_message_t **msg);

typedef struct deb_coeff_t deb_coeff_t;
DEB_API deb_status_t deb_create_coeff_with_preset(const deb_preset_t preset, deb_coeff_t **coeff);
DEB_API deb_status_t deb_create_coeff_with_size(const deb_size_t size, deb_coeff_t **coeff);
DEB_API deb_status_t deb_create_coeff_with_init(const deb_size_t size, const deb_real_t &init, deb_coeff_t **coeff);
DEB_API deb_status_t deb_destroy_coeff(deb_coeff_t **coeff);

typedef struct deb_poly_t deb_poly_t;
DEB_API deb_status_t deb_create_poly_with_preset(const deb_preset_t preset, const deb_size_t level, deb_poly_t **poly);
DEB_API deb_status_t deb_create_poly_with_prime(const deb_u64_t prime, const deb_size_t degree, deb_poly_t **poly);
DEB_API deb_status_t deb_destroy_poly(deb_poly_t **poly);

typedef struct deb_bigpoly_t deb_bigpoly_t;
DEB_API deb_status_t deb_create_bigpoly(const deb_preset_t preset, deb_bigpoly_t **bigpoly);
DEB_API deb_status_t deb_create_bigpoly_with_level(const deb_preset_t preset, const deb_size_t level, deb_bigpoly_t **bigpoly);
DEB_API deb_status_t deb_destroy_bigpoly(deb_bigpoly_t **bigpoly);

typedef struct deb_cipher_t deb_cipher_t;
DEB_API deb_status_t deb_create_cipher(const deb_preset_t preset, deb_cipher_t **cipher);
DEB_API deb_status_t deb_create_cipher_with_size(const deb_preset_t preset, const deb_size_t size, const deb_size_t level, deb_cipher_t **cipher);
DEB_API deb_status_t deb_destroy_cipher(deb_cipher_t **cipher);

typedef struct deb_sk_t deb_sk_t;
DEB_API deb_status_t deb_create_secretkey(const deb_preset_t preset, deb_sk_t **sk);
DEB_API deb_status_t deb_destroy_secretkey(deb_sk_t **sk);

typedef struct deb_swk_t deb_swk_t;
DEB_API deb_status_t deb_create_swk(const deb_preset_t preset, deb_swk_t **swk);
DEB_API deb_status_t deb_create_swk_with_type(const deb_preset_t preset, const deb_swk_kind_t type, deb_swk_t **swk);
DEB_API deb_status_t deb_destroy_swk(deb_swk_t **swk);

#ifdef __cplusplus
}
#endif

#endif // DEB_DEBTYPE_H
