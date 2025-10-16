# This file is dual licensed under the terms of the Apache License, Version
# 2.0, and the BSD License. See the LICENSE file in the root of this repository
# for complete details.

from __future__ import annotations

INCLUDES = """
#include <openssl/asn1.h>
"""

TYPES = """
typedef int... time_t;

typedef ... ASN1_INTEGER;

struct asn1_string_st {
    int length;
    int type;
    unsigned char *data;
    long flags;
};

typedef struct asn1_string_st ASN1_OCTET_STRING;
typedef struct asn1_string_st ASN1_IA5STRING;
typedef struct asn1_string_st ASN1_TIME;
typedef ... ASN1_OBJECT;
typedef struct asn1_string_st ASN1_STRING;
typedef ... ASN1_GENERALIZEDTIME;
typedef ... ASN1_ENUMERATED;

static const int V_ASN1_GENERALIZEDTIME;

static const int MBSTRING_UTF8;
"""

FUNCTIONS = """
/*  ASN1 STRING */
const unsigned char *ASN1_STRING_get0_data(const ASN1_STRING *);

/*  ASN1 INTEGER */
void ASN1_INTEGER_free(ASN1_INTEGER *);

/*  ASN1 TIME */
ASN1_TIME *ASN1_TIME_new(void);
void ASN1_TIME_free(ASN1_TIME *);
int ASN1_TIME_set_string(ASN1_TIME *, const char *);

/*  ASN1 GENERALIZEDTIME */
void ASN1_GENERALIZEDTIME_free(ASN1_GENERALIZEDTIME *);

int ASN1_STRING_type(const ASN1_STRING *);
int ASN1_STRING_to_UTF8(unsigned char **, const ASN1_STRING *);
int i2a_ASN1_INTEGER(BIO *, const ASN1_INTEGER *);

ASN1_GENERALIZEDTIME *ASN1_TIME_to_generalizedtime(const ASN1_TIME *,
                                                   ASN1_GENERALIZEDTIME **);

int ASN1_STRING_length(ASN1_STRING *);

BIGNUM *ASN1_INTEGER_to_BN(ASN1_INTEGER *, BIGNUM *);
ASN1_INTEGER *BN_to_ASN1_INTEGER(BIGNUM *, ASN1_INTEGER *);
"""

CUSTOMIZATIONS = """
"""
