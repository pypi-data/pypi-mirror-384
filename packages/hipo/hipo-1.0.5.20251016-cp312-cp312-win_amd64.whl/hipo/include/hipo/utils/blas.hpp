#pragma once


typedef int integer;
typedef double doublereal;
extern "C" {
int dsysv_(char *uplo, integer *n, integer *nrhs, doublereal 
*a, integer *lda, integer *ipiv, doublereal *b, integer *ldb, 
doublereal *work, integer *lwork, integer *info);
}
