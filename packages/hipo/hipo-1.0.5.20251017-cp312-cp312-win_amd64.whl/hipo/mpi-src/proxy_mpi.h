
#pragma once
#include <stdint.h>

#ifdef __cplusplus
extern "C" {
#endif

#ifdef PROXY_MPI_IMPORTS
#define MPI_COMM_NULL proxy_MPI_COMM_NULL
#define MPI_OP_NULL proxy_MPI_OP_NULL
#define MPI_GROUP_NULL proxy_MPI_GROUP_NULL
#define MPI_DATATYPE_NULL proxy_MPI_DATATYPE_NULL
#define MPI_REQUEST_NULL proxy_MPI_REQUEST_NULL
#define MPI_ERRHANDLER_NULL proxy_MPI_ERRHANDLER_NULL
#define MPI_IDENT proxy_MPI_IDENT
#define MPI_CONGRUENT proxy_MPI_CONGRUENT
#define MPI_SIMILAR proxy_MPI_SIMILAR
#define MPI_UNEQUAL proxy_MPI_UNEQUAL
#define MPI_CHAR proxy_MPI_CHAR
#define MPI_SIGNED_CHAR proxy_MPI_SIGNED_CHAR
#define MPI_UNSIGNED_CHAR proxy_MPI_UNSIGNED_CHAR
#define MPI_BYTE proxy_MPI_BYTE
#define MPI_WCHAR proxy_MPI_WCHAR
#define MPI_SHORT proxy_MPI_SHORT
#define MPI_UNSIGNED_SHORT proxy_MPI_UNSIGNED_SHORT
#define MPI_INT proxy_MPI_INT
#define MPI_UNSIGNED proxy_MPI_UNSIGNED
#define MPI_LONG proxy_MPI_LONG
#define MPI_UNSIGNED_LONG proxy_MPI_UNSIGNED_LONG
#define MPI_FLOAT proxy_MPI_FLOAT
#define MPI_DOUBLE proxy_MPI_DOUBLE
#define MPI_LONG_DOUBLE proxy_MPI_LONG_DOUBLE
#define MPI_LONG_LONG_INT proxy_MPI_LONG_LONG_INT
#define MPI_UNSIGNED_LONG_LONG proxy_MPI_UNSIGNED_LONG_LONG
#define MPI_LONG_LONG proxy_MPI_LONG_LONG
#define MPI_PACKED proxy_MPI_PACKED
#define MPI_FLOAT_INT proxy_MPI_FLOAT_INT
#define MPI_DOUBLE_INT proxy_MPI_DOUBLE_INT
#define MPI_LONG_INT proxy_MPI_LONG_INT
#define MPI_SHORT_INT proxy_MPI_SHORT_INT
#define MPI_2INT proxy_MPI_2INT
#define MPI_LONG_DOUBLE_INT proxy_MPI_LONG_DOUBLE_INT
#define MPI_COMPLEX proxy_MPI_COMPLEX
#define MPI_DOUBLE_COMPLEX proxy_MPI_DOUBLE_COMPLEX
#define MPI_LOGICAL proxy_MPI_LOGICAL
#define MPI_REAL proxy_MPI_REAL
#define MPI_DOUBLE_PRECISION proxy_MPI_DOUBLE_PRECISION
#define MPI_INTEGER proxy_MPI_INTEGER
#define MPI_2INTEGER proxy_MPI_2INTEGER
#define MPI_2REAL proxy_MPI_2REAL
#define MPI_2DOUBLE_PRECISION proxy_MPI_2DOUBLE_PRECISION
#define MPI_CHARACTER proxy_MPI_CHARACTER
#define MPI_REAL4 proxy_MPI_REAL4
#define MPI_REAL8 proxy_MPI_REAL8
#define MPI_COMPLEX8 proxy_MPI_COMPLEX8
#define MPI_COMPLEX16 proxy_MPI_COMPLEX16
#define MPI_INTEGER1 proxy_MPI_INTEGER1
#define MPI_INTEGER2 proxy_MPI_INTEGER2
#define MPI_INTEGER4 proxy_MPI_INTEGER4
#define MPI_INTEGER8 proxy_MPI_INTEGER8
#define MPI_INT8_T proxy_MPI_INT8_T
#define MPI_INT16_T proxy_MPI_INT16_T
#define MPI_INT32_T proxy_MPI_INT32_T
#define MPI_INT64_T proxy_MPI_INT64_T
#define MPI_UINT8_T proxy_MPI_UINT8_T
#define MPI_UINT16_T proxy_MPI_UINT16_T
#define MPI_UINT32_T proxy_MPI_UINT32_T
#define MPI_UINT64_T proxy_MPI_UINT64_T
#define MPI_C_BOOL proxy_MPI_C_BOOL
#define MPI_C_FLOAT_COMPLEX proxy_MPI_C_FLOAT_COMPLEX
#define MPI_C_COMPLEX proxy_MPI_C_COMPLEX
#define MPI_C_DOUBLE_COMPLEX proxy_MPI_C_DOUBLE_COMPLEX
#define MPI_C_LONG_DOUBLE_COMPLEX proxy_MPI_C_LONG_DOUBLE_COMPLEX
#define MPI_AINT proxy_MPI_AINT
#define MPI_OFFSET proxy_MPI_OFFSET
#define MPI_TYPECLASS_REAL proxy_MPI_TYPECLASS_REAL
#define MPI_TYPECLASS_INTEGER proxy_MPI_TYPECLASS_INTEGER
#define MPI_TYPECLASS_COMPLEX proxy_MPI_TYPECLASS_COMPLEX
#define MPI_COMM_WORLD proxy_MPI_COMM_WORLD
#define MPI_COMM_SELF proxy_MPI_COMM_SELF
#define MPI_GROUP_EMPTY proxy_MPI_GROUP_EMPTY
#define MPI_WIN_NULL proxy_MPI_WIN_NULL
#define MPI_FILE_NULL proxy_MPI_FILE_NULL
#define MPI_MAX proxy_MPI_MAX
#define MPI_MIN proxy_MPI_MIN
#define MPI_SUM proxy_MPI_SUM
#define MPI_PROD proxy_MPI_PROD
#define MPI_LAND proxy_MPI_LAND
#define MPI_BAND proxy_MPI_BAND
#define MPI_LOR proxy_MPI_LOR
#define MPI_BOR proxy_MPI_BOR
#define MPI_LXOR proxy_MPI_LXOR
#define MPI_BXOR proxy_MPI_BXOR
#define MPI_MINLOC proxy_MPI_MINLOC
#define MPI_MAXLOC proxy_MPI_MAXLOC
#define MPI_REPLACE proxy_MPI_REPLACE
#define MPI_TAG_UB proxy_MPI_TAG_UB
#define MPI_HOST proxy_MPI_HOST
#define MPI_IO proxy_MPI_IO
#define MPI_WTIME_IS_GLOBAL proxy_MPI_WTIME_IS_GLOBAL
#define MPI_UNIVERSE_SIZE proxy_MPI_UNIVERSE_SIZE
#define MPI_LASTUSEDCODE proxy_MPI_LASTUSEDCODE
#define MPI_APPNUM proxy_MPI_APPNUM
#define MPI_WIN_BASE proxy_MPI_WIN_BASE
#define MPI_WIN_SIZE proxy_MPI_WIN_SIZE
#define MPI_WIN_DISP_UNIT proxy_MPI_WIN_DISP_UNIT
#define MPI_MAX_PROCESSOR_NAME proxy_MPI_MAX_PROCESSOR_NAME
#define MPI_MAX_ERROR_STRING proxy_MPI_MAX_ERROR_STRING
#define MPI_MAX_PORT_NAME proxy_MPI_MAX_PORT_NAME
#define MPI_MAX_OBJECT_NAME proxy_MPI_MAX_OBJECT_NAME
#define MPI_UNDEFINED proxy_MPI_UNDEFINED
#define MPI_KEYVAL_INVALID proxy_MPI_KEYVAL_INVALID
#define MPI_BSEND_OVERHEAD proxy_MPI_BSEND_OVERHEAD
#define MPI_BOTTOM proxy_MPI_BOTTOM
#define MPI_PROC_NULL proxy_MPI_PROC_NULL
#define MPI_ANY_SOURCE proxy_MPI_ANY_SOURCE
#define MPI_ROOT proxy_MPI_ROOT
#define MPI_ANY_TAG proxy_MPI_ANY_TAG
#define MPI_LOCK_EXCLUSIVE proxy_MPI_LOCK_EXCLUSIVE
#define MPI_LOCK_SHARED proxy_MPI_LOCK_SHARED
#define MPI_ERRORS_ARE_FATAL proxy_MPI_ERRORS_ARE_FATAL
#define MPI_ERRORS_RETURN proxy_MPI_ERRORS_RETURN
#define MPI_NULL_COPY_FN proxy_MPI_NULL_COPY_FN
#define MPI_NULL_DELETE_FN proxy_MPI_NULL_DELETE_FN
#define MPI_DUP_FN proxy_MPI_DUP_FN
#define MPI_COMM_NULL_COPY_FN proxy_MPI_COMM_NULL_COPY_FN
#define MPI_COMM_NULL_DELETE_FN proxy_MPI_COMM_NULL_DELETE_FN
#define MPI_COMM_DUP_FN proxy_MPI_COMM_DUP_FN
#define MPI_WIN_NULL_COPY_FN proxy_MPI_WIN_NULL_COPY_FN
#define MPI_WIN_NULL_DELETE_FN proxy_MPI_WIN_NULL_DELETE_FN
#define MPI_WIN_DUP_FN proxy_MPI_WIN_DUP_FN
#define MPI_TYPE_NULL_COPY_FN proxy_MPI_TYPE_NULL_COPY_FN
#define MPI_TYPE_NULL_DELETE_FN proxy_MPI_TYPE_NULL_DELETE_FN
#define MPI_TYPE_DUP_FN proxy_MPI_TYPE_DUP_FN
#define MPI_INFO_NULL proxy_MPI_INFO_NULL
#define MPI_MAX_INFO_KEY proxy_MPI_MAX_INFO_KEY
#define MPI_MAX_INFO_VAL proxy_MPI_MAX_INFO_VAL
#define MPI_ORDER_C proxy_MPI_ORDER_C
#define MPI_ORDER_FORTRAN proxy_MPI_ORDER_FORTRAN
#define MPI_DISTRIBUTE_BLOCK proxy_MPI_DISTRIBUTE_BLOCK
#define MPI_DISTRIBUTE_CYCLIC proxy_MPI_DISTRIBUTE_CYCLIC
#define MPI_DISTRIBUTE_NONE proxy_MPI_DISTRIBUTE_NONE
#define MPI_DISTRIBUTE_DFLT_DARG proxy_MPI_DISTRIBUTE_DFLT_DARG
#define MPI_IN_PLACE proxy_MPI_IN_PLACE
#define MPI_MODE_NOCHECK proxy_MPI_MODE_NOCHECK
#define MPI_MODE_NOSTORE proxy_MPI_MODE_NOSTORE
#define MPI_MODE_NOPUT proxy_MPI_MODE_NOPUT
#define MPI_MODE_NOPRECEDE proxy_MPI_MODE_NOPRECEDE
#define MPI_MODE_NOSUCCEED proxy_MPI_MODE_NOSUCCEED
#define MPI_Comm_c2f proxy_MPI_Comm_c2f
#define MPI_Comm_f2c proxy_MPI_Comm_f2c
#define MPI_Type_c2f proxy_MPI_Type_c2f
#define MPI_Type_f2c proxy_MPI_Type_f2c
#define MPI_Group_c2f proxy_MPI_Group_c2f
#define MPI_Group_f2c proxy_MPI_Group_f2c
#define MPI_Info_f2c proxy_MPI_Info_f2c
#define MPI_Request_f2c proxy_MPI_Request_f2c
#define MPI_Request_c2f proxy_MPI_Request_c2f
#define MPI_Op_c2f proxy_MPI_Op_c2f
#define MPI_Op_f2c proxy_MPI_Op_f2c
#define MPI_Errhandler_c2f proxy_MPI_Errhandler_c2f
#define MPI_Errhandler_f2c proxy_MPI_Errhandler_f2c
#define MPI_Win_c2f proxy_MPI_Win_c2f
#define MPI_Win_f2c proxy_MPI_Win_f2c
#define MPI_STATUS_IGNORE proxy_MPI_STATUS_IGNORE
#define MPI_STATUSES_IGNORE proxy_MPI_STATUSES_IGNORE
#define MPI_ERRCODES_IGNORE proxy_MPI_ERRCODES_IGNORE
#define MPI_ARGV_NULL proxy_MPI_ARGV_NULL
#define MPI_ARGVS_NULL proxy_MPI_ARGVS_NULL
#define MPI_THREAD_SINGLE proxy_MPI_THREAD_SINGLE
#define MPI_THREAD_FUNNELED proxy_MPI_THREAD_FUNNELED
#define MPI_THREAD_SERIALIZED proxy_MPI_THREAD_SERIALIZED
#define MPI_THREAD_MULTIPLE proxy_MPI_THREAD_MULTIPLE
#define MPI_SUCCESS proxy_MPI_SUCCESS
#define MPI_ERR_BUFFER proxy_MPI_ERR_BUFFER
#define MPI_ERR_COUNT proxy_MPI_ERR_COUNT
#define MPI_ERR_TYPE proxy_MPI_ERR_TYPE
#define MPI_ERR_TAG proxy_MPI_ERR_TAG
#define MPI_ERR_COMM proxy_MPI_ERR_COMM
#define MPI_ERR_RANK proxy_MPI_ERR_RANK
#define MPI_ERR_ROOT proxy_MPI_ERR_ROOT
#define MPI_ERR_TRUNCATE proxy_MPI_ERR_TRUNCATE
#define MPI_ERR_GROUP proxy_MPI_ERR_GROUP
#define MPI_ERR_OP proxy_MPI_ERR_OP
#define MPI_ERR_REQUEST proxy_MPI_ERR_REQUEST
#define MPI_ERR_TOPOLOGY proxy_MPI_ERR_TOPOLOGY
#define MPI_ERR_DIMS proxy_MPI_ERR_DIMS
#define MPI_ERR_ARG proxy_MPI_ERR_ARG
#define MPI_ERR_OTHER proxy_MPI_ERR_OTHER
#define MPI_ERR_UNKNOWN proxy_MPI_ERR_UNKNOWN
#define MPI_ERR_INTERN proxy_MPI_ERR_INTERN
#define MPI_ERR_IN_STATUS proxy_MPI_ERR_IN_STATUS
#define MPI_ERR_PENDING proxy_MPI_ERR_PENDING
#define MPI_ERR_ACCESS proxy_MPI_ERR_ACCESS
#define MPI_ERR_AMODE proxy_MPI_ERR_AMODE
#define MPI_ERR_BAD_FILE proxy_MPI_ERR_BAD_FILE
#define MPI_ERR_CONVERSION proxy_MPI_ERR_CONVERSION
#define MPI_ERR_DUP_DATAREP proxy_MPI_ERR_DUP_DATAREP
#define MPI_ERR_FILE_EXISTS proxy_MPI_ERR_FILE_EXISTS
#define MPI_ERR_FILE_IN_USE proxy_MPI_ERR_FILE_IN_USE
#define MPI_ERR_FILE proxy_MPI_ERR_FILE
#define MPI_ERR_IO proxy_MPI_ERR_IO
#define MPI_ERR_NO_SPACE proxy_MPI_ERR_NO_SPACE
#define MPI_ERR_NO_SUCH_FILE proxy_MPI_ERR_NO_SUCH_FILE
#define MPI_ERR_READ_ONLY proxy_MPI_ERR_READ_ONLY
#define MPI_ERR_UNSUPPORTED_DATAREP proxy_MPI_ERR_UNSUPPORTED_DATAREP
#define MPI_ERR_INFO proxy_MPI_ERR_INFO
#define MPI_ERR_INFO_KEY proxy_MPI_ERR_INFO_KEY
#define MPI_ERR_INFO_VALUE proxy_MPI_ERR_INFO_VALUE
#define MPI_ERR_INFO_NOKEY proxy_MPI_ERR_INFO_NOKEY
#define MPI_ERR_NAME proxy_MPI_ERR_NAME
#define MPI_ERR_NO_MEM proxy_MPI_ERR_NO_MEM
#define MPI_ERR_NOT_SAME proxy_MPI_ERR_NOT_SAME
#define MPI_ERR_PORT proxy_MPI_ERR_PORT
#define MPI_ERR_QUOTA proxy_MPI_ERR_QUOTA
#define MPI_ERR_SERVICE proxy_MPI_ERR_SERVICE
#define MPI_ERR_SPAWN proxy_MPI_ERR_SPAWN
#define MPI_ERR_UNSUPPORTED_OPERATION proxy_MPI_ERR_UNSUPPORTED_OPERATION
#define MPI_ERR_WIN proxy_MPI_ERR_WIN
#define MPI_ERR_BASE proxy_MPI_ERR_BASE
#define MPI_ERR_LOCKTYPE proxy_MPI_ERR_LOCKTYPE
#define MPI_ERR_KEYVAL proxy_MPI_ERR_KEYVAL
#define MPI_ERR_RMA_CONFLICT proxy_MPI_ERR_RMA_CONFLICT
#define MPI_ERR_RMA_SYNC proxy_MPI_ERR_RMA_SYNC
#define MPI_ERR_SIZE proxy_MPI_ERR_SIZE
#define MPI_ERR_DISP proxy_MPI_ERR_DISP
#define MPI_ERR_ASSERT proxy_MPI_ERR_ASSERT
#define MPI_ERR_LASTCODE proxy_MPI_ERR_LASTCODE
#define MPI_CONVERSION_FN_NULL proxy_MPI_CONVERSION_FN_NULL
#define MPI_MODE_RDONLY proxy_MPI_MODE_RDONLY
#define MPI_MODE_RDWR proxy_MPI_MODE_RDWR
#define MPI_MODE_WRONLY proxy_MPI_MODE_WRONLY
#define MPI_MODE_CREATE proxy_MPI_MODE_CREATE
#define MPI_MODE_EXCL proxy_MPI_MODE_EXCL
#define MPI_MODE_DELETE_ON_CLOSE proxy_MPI_MODE_DELETE_ON_CLOSE
#define MPI_MODE_UNIQUE_OPEN proxy_MPI_MODE_UNIQUE_OPEN
#define MPI_MODE_APPEND proxy_MPI_MODE_APPEND
#define MPI_MODE_SEQUENTIAL proxy_MPI_MODE_SEQUENTIAL
#define MPI_DISPLACEMENT_CURRENT proxy_MPI_DISPLACEMENT_CURRENT
#define MPI_SEEK_SET proxy_MPI_SEEK_SET
#define MPI_SEEK_CUR proxy_MPI_SEEK_CUR
#define MPI_SEEK_END proxy_MPI_SEEK_END
#define MPI_MAX_DATAREP_STRING proxy_MPI_MAX_DATAREP_STRING
#define MPI_Datatype proxy_MPI_Datatype
#define MPI_Comm proxy_MPI_Comm
#define MPI_Group proxy_MPI_Group
#define MPI_Win proxy_MPI_Win
#define MPI_File proxy_MPI_File
#define MPI_Op proxy_MPI_Op
#define MPI_UNWEIGHTED proxy_MPI_UNWEIGHTED
#define MPI_WEIGHTS_EMPTY proxy_MPI_WEIGHTS_EMPTY
#define MPI_Handler_function proxy_MPI_Handler_function
#define MPI_Comm_copy_attr_function proxy_MPI_Comm_copy_attr_function
#define MPI_Comm_delete_attr_function proxy_MPI_Comm_delete_attr_function
#define MPI_Type_copy_attr_function proxy_MPI_Type_copy_attr_function
#define MPI_Type_delete_attr_function proxy_MPI_Type_delete_attr_function
#define MPI_Win_copy_attr_function proxy_MPI_Win_copy_attr_function
#define MPI_Win_delete_attr_function proxy_MPI_Win_delete_attr_function
#define MPI_Comm_errhandler_function proxy_MPI_Comm_errhandler_function
#define MPI_File_errhandler_function proxy_MPI_File_errhandler_function
#define MPI_Win_errhandler_function proxy_MPI_Win_errhandler_function
#define MPI_Comm_errhandler_fn proxy_MPI_Comm_errhandler_fn
#define MPI_File_errhandler_fn proxy_MPI_File_errhandler_fn
#define MPI_Win_errhandler_fn proxy_MPI_Win_errhandler_fn
#define MPI_Errhandler proxy_MPI_Errhandler
#define MPI_Request proxy_MPI_Request
#define MPI_Copy_function proxy_MPI_Copy_function
#define MPI_Delete_function proxy_MPI_Delete_function
#define MPI_Info proxy_MPI_Info
#define MPI_Aint proxy_MPI_Aint
#define MPI_Fint proxy_MPI_Fint
#define MPI_Offset proxy_MPI_Offset
#define MPI_Status proxy_MPI_Status
#define MPI_User_function proxy_MPI_User_function
#define MPI_F_STATUS_IGNORE proxy_MPI_F_STATUS_IGNORE
#define MPI_F_STATUSES_IGNORE proxy_MPI_F_STATUSES_IGNORE
#define MPI_Grequest_cancel_function proxy_MPI_Grequest_cancel_function
#define MPI_Grequest_free_function proxy_MPI_Grequest_free_function
#define MPI_Grequest_query_function proxy_MPI_Grequest_query_function
#define MPI_Datarep_conversion_function proxy_MPI_Datarep_conversion_function
#define MPI_Datarep_extent_function proxy_MPI_Datarep_extent_function
#define MPI_Status_c2f proxy_MPI_Status_c2f
#define MPI_Status_f2c proxy_MPI_Status_f2c
#define MPI_Type_create_f90_integer proxy_MPI_Type_create_f90_integer
#define MPI_Type_create_f90_real proxy_MPI_Type_create_f90_real
#define MPI_Type_create_f90_complex proxy_MPI_Type_create_f90_complex
#define MPI_Attr_delete proxy_MPI_Attr_delete
#define MPI_Attr_get proxy_MPI_Attr_get
#define MPI_Attr_put proxy_MPI_Attr_put
#define MPI_Comm_create_keyval proxy_MPI_Comm_create_keyval
#define MPI_Comm_delete_attr proxy_MPI_Comm_delete_attr
#define MPI_Comm_free_keyval proxy_MPI_Comm_free_keyval
#define MPI_Comm_get_attr proxy_MPI_Comm_get_attr
#define MPI_Comm_set_attr proxy_MPI_Comm_set_attr
#define MPI_Keyval_create proxy_MPI_Keyval_create
#define MPI_Keyval_free proxy_MPI_Keyval_free
#define MPI_Type_create_keyval proxy_MPI_Type_create_keyval
#define MPI_Type_delete_attr proxy_MPI_Type_delete_attr
#define MPI_Type_free_keyval proxy_MPI_Type_free_keyval
#define MPI_Type_get_attr proxy_MPI_Type_get_attr
#define MPI_Type_set_attr proxy_MPI_Type_set_attr
#define MPI_Win_create_keyval proxy_MPI_Win_create_keyval
#define MPI_Win_delete_attr proxy_MPI_Win_delete_attr
#define MPI_Win_free_keyval proxy_MPI_Win_free_keyval
#define MPI_Win_get_attr proxy_MPI_Win_get_attr
#define MPI_Win_set_attr proxy_MPI_Win_set_attr
#define MPI_Allgather proxy_MPI_Allgather
#define MPI_Allgatherv proxy_MPI_Allgatherv
#define MPI_Allreduce proxy_MPI_Allreduce
#define MPI_Alltoall proxy_MPI_Alltoall
#define MPI_Alltoallv proxy_MPI_Alltoallv
#define MPI_Alltoallw proxy_MPI_Alltoallw
#define MPI_Barrier proxy_MPI_Barrier
#define MPI_Bcast proxy_MPI_Bcast
#define MPI_Exscan proxy_MPI_Exscan
#define MPI_Gather proxy_MPI_Gather
#define MPI_Gatherv proxy_MPI_Gatherv
#define MPI_Reduce proxy_MPI_Reduce
#define MPI_Reduce_local proxy_MPI_Reduce_local
#define MPI_Reduce_scatter proxy_MPI_Reduce_scatter
#define MPI_Scan proxy_MPI_Scan
#define MPI_Scatter proxy_MPI_Scatter
#define MPI_Scatterv proxy_MPI_Scatterv
#define MPI_Comm_compare proxy_MPI_Comm_compare
#define MPI_Comm_create proxy_MPI_Comm_create
#define MPI_Comm_dup proxy_MPI_Comm_dup
#define MPI_Comm_free proxy_MPI_Comm_free
#define MPI_Comm_get_name proxy_MPI_Comm_get_name
#define MPI_Comm_group proxy_MPI_Comm_group
#define MPI_Comm_rank proxy_MPI_Comm_rank
#define MPI_Comm_remote_group proxy_MPI_Comm_remote_group
#define MPI_Comm_remote_size proxy_MPI_Comm_remote_size
#define MPI_Comm_set_name proxy_MPI_Comm_set_name
#define MPI_Comm_size proxy_MPI_Comm_size
#define MPI_Comm_split proxy_MPI_Comm_split
#define MPI_Comm_test_inter proxy_MPI_Comm_test_inter
#define MPI_Intercomm_create proxy_MPI_Intercomm_create
#define MPI_Intercomm_merge proxy_MPI_Intercomm_merge
#define MPI_Get_address proxy_MPI_Get_address
#define MPI_Get_count proxy_MPI_Get_count
#define MPI_Get_elements proxy_MPI_Get_elements
#define MPI_Pack proxy_MPI_Pack
#define MPI_Pack_external proxy_MPI_Pack_external
#define MPI_Pack_external_size proxy_MPI_Pack_external_size
#define MPI_Pack_size proxy_MPI_Pack_size
#define MPI_Status_set_elements proxy_MPI_Status_set_elements
#define MPI_Type_commit proxy_MPI_Type_commit
#define MPI_Type_contiguous proxy_MPI_Type_contiguous
#define MPI_Type_create_darray proxy_MPI_Type_create_darray
#define MPI_Type_create_hindexed proxy_MPI_Type_create_hindexed
#define MPI_Type_create_hvector proxy_MPI_Type_create_hvector
#define MPI_Type_create_indexed_block proxy_MPI_Type_create_indexed_block
#define MPI_Type_create_resized proxy_MPI_Type_create_resized
#define MPI_Type_create_struct proxy_MPI_Type_create_struct
#define MPI_Type_create_subarray proxy_MPI_Type_create_subarray
#define MPI_Type_dup proxy_MPI_Type_dup
#define MPI_Type_free proxy_MPI_Type_free
#define MPI_Type_get_contents proxy_MPI_Type_get_contents
#define MPI_Type_get_envelope proxy_MPI_Type_get_envelope
#define MPI_Type_get_extent proxy_MPI_Type_get_extent
#define MPI_Type_get_name proxy_MPI_Type_get_name
#define MPI_Type_get_true_extent proxy_MPI_Type_get_true_extent
#define MPI_Type_indexed proxy_MPI_Type_indexed
#define MPI_Type_match_size proxy_MPI_Type_match_size
#define MPI_Type_set_name proxy_MPI_Type_set_name
#define MPI_Type_size proxy_MPI_Type_size
#define MPI_Type_vector proxy_MPI_Type_vector
#define MPI_Unpack proxy_MPI_Unpack
#define MPI_Unpack_external proxy_MPI_Unpack_external
#define MPI_Add_error_class proxy_MPI_Add_error_class
#define MPI_Add_error_code proxy_MPI_Add_error_code
#define MPI_Add_error_string proxy_MPI_Add_error_string
#define MPI_Comm_call_errhandler proxy_MPI_Comm_call_errhandler
#define MPI_Comm_create_errhandler proxy_MPI_Comm_create_errhandler
#define MPI_Comm_get_errhandler proxy_MPI_Comm_get_errhandler
#define MPI_Comm_set_errhandler proxy_MPI_Comm_set_errhandler
#define MPI_Errhandler_free proxy_MPI_Errhandler_free
#define MPI_Error_class proxy_MPI_Error_class
#define MPI_Error_string proxy_MPI_Error_string
#define MPI_File_call_errhandler proxy_MPI_File_call_errhandler
#define MPI_File_create_errhandler proxy_MPI_File_create_errhandler
#define MPI_File_get_errhandler proxy_MPI_File_get_errhandler
#define MPI_File_set_errhandler proxy_MPI_File_set_errhandler
#define MPI_Win_call_errhandler proxy_MPI_Win_call_errhandler
#define MPI_Win_create_errhandler proxy_MPI_Win_create_errhandler
#define MPI_Win_get_errhandler proxy_MPI_Win_get_errhandler
#define MPI_Win_set_errhandler proxy_MPI_Win_set_errhandler
#define MPI_Group_compare proxy_MPI_Group_compare
#define MPI_Group_difference proxy_MPI_Group_difference
#define MPI_Group_excl proxy_MPI_Group_excl
#define MPI_Group_free proxy_MPI_Group_free
#define MPI_Group_incl proxy_MPI_Group_incl
#define MPI_Group_intersection proxy_MPI_Group_intersection
#define MPI_Group_range_excl proxy_MPI_Group_range_excl
#define MPI_Group_range_incl proxy_MPI_Group_range_incl
#define MPI_Group_rank proxy_MPI_Group_rank
#define MPI_Group_size proxy_MPI_Group_size
#define MPI_Group_translate_ranks proxy_MPI_Group_translate_ranks
#define MPI_Group_union proxy_MPI_Group_union
#define MPI_Info_create proxy_MPI_Info_create
#define MPI_Info_delete proxy_MPI_Info_delete
#define MPI_Info_dup proxy_MPI_Info_dup
#define MPI_Info_free proxy_MPI_Info_free
#define MPI_Info_get proxy_MPI_Info_get
#define MPI_Info_get_nkeys proxy_MPI_Info_get_nkeys
#define MPI_Info_get_nthkey proxy_MPI_Info_get_nthkey
#define MPI_Info_get_valuelen proxy_MPI_Info_get_valuelen
#define MPI_Info_set proxy_MPI_Info_set
#define MPI_Abort proxy_MPI_Abort
#define MPI_Finalize proxy_MPI_Finalize
#define MPI_Finalized proxy_MPI_Finalized
#define MPI_Init proxy_MPI_Init
#define MPI_Init_thread proxy_MPI_Init_thread
#define MPI_Initialized proxy_MPI_Initialized
#define MPI_Is_thread_main proxy_MPI_Is_thread_main
#define MPI_Query_thread proxy_MPI_Query_thread
#define MPI_Get_processor_name proxy_MPI_Get_processor_name
#define MPI_Get_version proxy_MPI_Get_version
#define MPI_Pcontrol proxy_MPI_Pcontrol
#define MPI_Op_commutative proxy_MPI_Op_commutative
#define MPI_Op_create proxy_MPI_Op_create
#define MPI_Op_free proxy_MPI_Op_free
#define MPI_Bsend proxy_MPI_Bsend
#define MPI_Bsend_init proxy_MPI_Bsend_init
#define MPI_Buffer_attach proxy_MPI_Buffer_attach
#define MPI_Buffer_detach proxy_MPI_Buffer_detach
#define MPI_Ibsend proxy_MPI_Ibsend
#define MPI_Iprobe proxy_MPI_Iprobe
#define MPI_Irecv proxy_MPI_Irecv
#define MPI_Irsend proxy_MPI_Irsend
#define MPI_Isend proxy_MPI_Isend
#define MPI_Issend proxy_MPI_Issend
#define MPI_Probe proxy_MPI_Probe
#define MPI_Recv proxy_MPI_Recv
#define MPI_Recv_init proxy_MPI_Recv_init
#define MPI_Rsend proxy_MPI_Rsend
#define MPI_Rsend_init proxy_MPI_Rsend_init
#define MPI_Send proxy_MPI_Send
#define MPI_Send_init proxy_MPI_Send_init
#define MPI_Sendrecv proxy_MPI_Sendrecv
#define MPI_Sendrecv_replace proxy_MPI_Sendrecv_replace
#define MPI_Ssend proxy_MPI_Ssend
#define MPI_Ssend_init proxy_MPI_Ssend_init
#define MPI_Cancel proxy_MPI_Cancel
#define MPI_Grequest_complete proxy_MPI_Grequest_complete
#define MPI_Grequest_start proxy_MPI_Grequest_start
#define MPI_Request_free proxy_MPI_Request_free
#define MPI_Request_get_status proxy_MPI_Request_get_status
#define MPI_Start proxy_MPI_Start
#define MPI_Startall proxy_MPI_Startall
#define MPI_Status_set_cancelled proxy_MPI_Status_set_cancelled
#define MPI_Test proxy_MPI_Test
#define MPI_Test_cancelled proxy_MPI_Test_cancelled
#define MPI_Testall proxy_MPI_Testall
#define MPI_Testany proxy_MPI_Testany
#define MPI_Testsome proxy_MPI_Testsome
#define MPI_Wait proxy_MPI_Wait
#define MPI_Waitall proxy_MPI_Waitall
#define MPI_Waitany proxy_MPI_Waitany
#define MPI_Waitsome proxy_MPI_Waitsome
#define MPI_Accumulate proxy_MPI_Accumulate
#define MPI_Alloc_mem proxy_MPI_Alloc_mem
#define MPI_Free_mem proxy_MPI_Free_mem
#define MPI_Get proxy_MPI_Get
#define MPI_Put proxy_MPI_Put
#define MPI_Win_complete proxy_MPI_Win_complete
#define MPI_Win_create proxy_MPI_Win_create
#define MPI_Win_fence proxy_MPI_Win_fence
#define MPI_Win_free proxy_MPI_Win_free
#define MPI_Win_get_group proxy_MPI_Win_get_group
#define MPI_Win_get_name proxy_MPI_Win_get_name
#define MPI_Win_lock proxy_MPI_Win_lock
#define MPI_Win_post proxy_MPI_Win_post
#define MPI_Win_set_name proxy_MPI_Win_set_name
#define MPI_Win_start proxy_MPI_Win_start
#define MPI_Win_test proxy_MPI_Win_test
#define MPI_Win_unlock proxy_MPI_Win_unlock
#define MPI_Win_wait proxy_MPI_Win_wait
#define MPI_Close_port proxy_MPI_Close_port
#define MPI_Comm_accept proxy_MPI_Comm_accept
#define MPI_Comm_connect proxy_MPI_Comm_connect
#define MPI_Comm_disconnect proxy_MPI_Comm_disconnect
#define MPI_Comm_get_parent proxy_MPI_Comm_get_parent
#define MPI_Comm_join proxy_MPI_Comm_join
#define MPI_Comm_spawn proxy_MPI_Comm_spawn
#define MPI_Comm_spawn_multiple proxy_MPI_Comm_spawn_multiple
#define MPI_Lookup_name proxy_MPI_Lookup_name
#define MPI_Open_port proxy_MPI_Open_port
#define MPI_Publish_name proxy_MPI_Publish_name
#define MPI_Unpublish_name proxy_MPI_Unpublish_name
#define MPI_Wtick proxy_MPI_Wtick
#define MPI_Wtime proxy_MPI_Wtime
#define MPI_Cart_coords proxy_MPI_Cart_coords
#define MPI_Cart_create proxy_MPI_Cart_create
#define MPI_Cart_get proxy_MPI_Cart_get
#define MPI_Cart_map proxy_MPI_Cart_map
#define MPI_Cart_rank proxy_MPI_Cart_rank
#define MPI_Cart_shift proxy_MPI_Cart_shift
#define MPI_Cart_sub proxy_MPI_Cart_sub
#define MPI_Cartdim_get proxy_MPI_Cartdim_get
#define MPI_Dims_create proxy_MPI_Dims_create
#define MPI_Graph_create proxy_MPI_Graph_create
#define MPI_Graph_get proxy_MPI_Graph_get
#define MPI_Graph_map proxy_MPI_Graph_map
#define MPI_Graph_neighbors proxy_MPI_Graph_neighbors
#define MPI_Graph_neighbors_count proxy_MPI_Graph_neighbors_count
#define MPI_Graphdims_get proxy_MPI_Graphdims_get
#define MPI_Topo_test proxy_MPI_Topo_test
#define MPI_Allgather_c proxy_MPI_Allgather_c
#define MPI_Allgatherv_c proxy_MPI_Allgatherv_c
#define MPI_Allreduce_c proxy_MPI_Allreduce_c
#define MPI_Alltoall_c proxy_MPI_Alltoall_c
#define MPI_Alltoallv_c proxy_MPI_Alltoallv_c
#define MPI_Alltoallw_c proxy_MPI_Alltoallw_c
#define MPI_Bcast_c proxy_MPI_Bcast_c
#define MPI_Exscan_c proxy_MPI_Exscan_c
#define MPI_Gather_c proxy_MPI_Gather_c
#define MPI_Gatherv_c proxy_MPI_Gatherv_c
#define MPI_Reduce_c proxy_MPI_Reduce_c
#define MPI_Reduce_local_c proxy_MPI_Reduce_local_c
#define MPI_Reduce_scatter_c proxy_MPI_Reduce_scatter_c
#define MPI_Scan_c proxy_MPI_Scan_c
#define MPI_Scatter_c proxy_MPI_Scatter_c
#define MPI_Scatterv_c proxy_MPI_Scatterv_c
#define MPI_Get_count_c proxy_MPI_Get_count_c
#define MPI_Get_elements_c proxy_MPI_Get_elements_c
#define MPI_Pack_c proxy_MPI_Pack_c
#define MPI_Pack_external_c proxy_MPI_Pack_external_c
#define MPI_Pack_external_size_c proxy_MPI_Pack_external_size_c
#define MPI_Pack_size_c proxy_MPI_Pack_size_c
#define MPI_Type_contiguous_c proxy_MPI_Type_contiguous_c
#define MPI_Type_create_darray_c proxy_MPI_Type_create_darray_c
#define MPI_Type_create_hindexed_c proxy_MPI_Type_create_hindexed_c
#define MPI_Type_create_hvector_c proxy_MPI_Type_create_hvector_c
#define MPI_Type_create_indexed_block_c proxy_MPI_Type_create_indexed_block_c
#define MPI_Type_create_resized_c proxy_MPI_Type_create_resized_c
#define MPI_Type_create_struct_c proxy_MPI_Type_create_struct_c
#define MPI_Type_create_subarray_c proxy_MPI_Type_create_subarray_c
#define MPI_Type_get_contents_c proxy_MPI_Type_get_contents_c
#define MPI_Type_get_envelope_c proxy_MPI_Type_get_envelope_c
#define MPI_Type_get_extent_c proxy_MPI_Type_get_extent_c
#define MPI_Type_get_true_extent_c proxy_MPI_Type_get_true_extent_c
#define MPI_Type_indexed_c proxy_MPI_Type_indexed_c
#define MPI_Type_size_c proxy_MPI_Type_size_c
#define MPI_Type_vector_c proxy_MPI_Type_vector_c
#define MPI_Unpack_c proxy_MPI_Unpack_c
#define MPI_Unpack_external_c proxy_MPI_Unpack_external_c
#define MPI_Op_create_c proxy_MPI_Op_create_c
#define MPI_Bsend_c proxy_MPI_Bsend_c
#define MPI_Bsend_init_c proxy_MPI_Bsend_init_c
#define MPI_Buffer_attach_c proxy_MPI_Buffer_attach_c
#define MPI_Buffer_detach_c proxy_MPI_Buffer_detach_c
#define MPI_Ibsend_c proxy_MPI_Ibsend_c
#define MPI_Irecv_c proxy_MPI_Irecv_c
#define MPI_Irsend_c proxy_MPI_Irsend_c
#define MPI_Isend_c proxy_MPI_Isend_c
#define MPI_Issend_c proxy_MPI_Issend_c
#define MPI_Recv_c proxy_MPI_Recv_c
#define MPI_Recv_init_c proxy_MPI_Recv_init_c
#define MPI_Rsend_c proxy_MPI_Rsend_c
#define MPI_Rsend_init_c proxy_MPI_Rsend_init_c
#define MPI_Send_c proxy_MPI_Send_c
#define MPI_Send_init_c proxy_MPI_Send_init_c
#define MPI_Sendrecv_c proxy_MPI_Sendrecv_c
#define MPI_Sendrecv_replace_c proxy_MPI_Sendrecv_replace_c
#define MPI_Ssend_c proxy_MPI_Ssend_c
#define MPI_Ssend_init_c proxy_MPI_Ssend_init_c
#define MPI_Accumulate_c proxy_MPI_Accumulate_c
#define MPI_Get_c proxy_MPI_Get_c
#define MPI_Put_c proxy_MPI_Put_c
#define MPI_Win_create_c proxy_MPI_Win_create_c
#define MPI_File_open proxy_MPI_File_open
#define MPI_File_close proxy_MPI_File_close
#define MPI_File_delete proxy_MPI_File_delete
#define MPI_File_set_size proxy_MPI_File_set_size
#define MPI_File_preallocate proxy_MPI_File_preallocate
#define MPI_File_get_size proxy_MPI_File_get_size
#define MPI_File_get_group proxy_MPI_File_get_group
#define MPI_File_get_amode proxy_MPI_File_get_amode
#define MPI_File_set_info proxy_MPI_File_set_info
#define MPI_File_get_info proxy_MPI_File_get_info
#define MPI_File_set_view proxy_MPI_File_set_view
#define MPI_File_get_view proxy_MPI_File_get_view
#define MPI_File_read_at proxy_MPI_File_read_at
#define MPI_File_read_at_all proxy_MPI_File_read_at_all
#define MPI_File_write_at proxy_MPI_File_write_at
#define MPI_File_write_at_all proxy_MPI_File_write_at_all
#define MPI_File_iread_at proxy_MPI_File_iread_at
#define MPI_File_iwrite_at proxy_MPI_File_iwrite_at
#define MPI_File_read proxy_MPI_File_read
#define MPI_File_read_all proxy_MPI_File_read_all
#define MPI_File_write proxy_MPI_File_write
#define MPI_File_write_all proxy_MPI_File_write_all
#define MPI_File_iread proxy_MPI_File_iread
#define MPI_File_iwrite proxy_MPI_File_iwrite
#define MPI_File_seek proxy_MPI_File_seek
#define MPI_File_get_position proxy_MPI_File_get_position
#define MPI_File_get_byte_offset proxy_MPI_File_get_byte_offset
#define MPI_File_read_shared proxy_MPI_File_read_shared
#define MPI_File_write_shared proxy_MPI_File_write_shared
#define MPI_File_iread_shared proxy_MPI_File_iread_shared
#define MPI_File_iwrite_shared proxy_MPI_File_iwrite_shared
#define MPI_File_read_ordered proxy_MPI_File_read_ordered
#define MPI_File_write_ordered proxy_MPI_File_write_ordered
#define MPI_File_seek_shared proxy_MPI_File_seek_shared
#define MPI_File_get_position_shared proxy_MPI_File_get_position_shared
#define MPI_File_read_at_all_begin proxy_MPI_File_read_at_all_begin
#define MPI_File_read_at_all_end proxy_MPI_File_read_at_all_end
#define MPI_File_write_at_all_begin proxy_MPI_File_write_at_all_begin
#define MPI_File_write_at_all_end proxy_MPI_File_write_at_all_end
#define MPI_File_read_all_begin proxy_MPI_File_read_all_begin
#define MPI_File_read_all_end proxy_MPI_File_read_all_end
#define MPI_File_write_all_begin proxy_MPI_File_write_all_begin
#define MPI_File_write_all_end proxy_MPI_File_write_all_end
#define MPI_File_read_ordered_begin proxy_MPI_File_read_ordered_begin
#define MPI_File_read_ordered_end proxy_MPI_File_read_ordered_end
#define MPI_File_write_ordered_begin proxy_MPI_File_write_ordered_begin
#define MPI_File_write_ordered_end proxy_MPI_File_write_ordered_end
#define MPI_File_get_type_extent proxy_MPI_File_get_type_extent
#define MPI_Register_datarep proxy_MPI_Register_datarep
#define MPI_File_set_atomicity proxy_MPI_File_set_atomicity
#define MPI_File_get_atomicity proxy_MPI_File_get_atomicity
#define MPI_File_sync proxy_MPI_File_sync
#define MPI_File_read_c proxy_MPI_File_read_c
#define MPI_File_read_all_c proxy_MPI_File_read_all_c
#define MPI_File_read_all_begin_c proxy_MPI_File_read_all_begin_c
#define MPI_File_read_at_c proxy_MPI_File_read_at_c
#define MPI_File_read_at_all_c proxy_MPI_File_read_at_all_c
#define MPI_File_read_at_all_begin_c proxy_MPI_File_read_at_all_begin_c
#define MPI_File_read_ordered_c proxy_MPI_File_read_ordered_c
#define MPI_File_read_ordered_begin_c proxy_MPI_File_read_ordered_begin_c
#define MPI_File_read_shared_c proxy_MPI_File_read_shared_c
#define MPI_File_write_c proxy_MPI_File_write_c
#define MPI_File_write_all_c proxy_MPI_File_write_all_c
#define MPI_File_write_all_begin_c proxy_MPI_File_write_all_begin_c
#define MPI_File_write_at_c proxy_MPI_File_write_at_c
#define MPI_File_write_at_all_c proxy_MPI_File_write_at_all_c
#define MPI_File_write_at_all_begin_c proxy_MPI_File_write_at_all_begin_c
#define MPI_File_write_ordered_c proxy_MPI_File_write_ordered_c
#define MPI_File_write_ordered_begin_c proxy_MPI_File_write_ordered_begin_c
#define MPI_File_write_shared_c proxy_MPI_File_write_shared_c
#define MPI_File_iread_c proxy_MPI_File_iread_c
#define MPI_File_iread_at_c proxy_MPI_File_iread_at_c
#define MPI_File_iread_shared_c proxy_MPI_File_iread_shared_c
#define MPI_File_iwrite_c proxy_MPI_File_iwrite_c
#define MPI_File_iwrite_at_c proxy_MPI_File_iwrite_at_c
#define MPI_File_iwrite_shared_c proxy_MPI_File_iwrite_shared_c
#define MPI_File_get_type_extent_c proxy_MPI_File_get_type_extent_c
#define MPI_Register_datarep_c proxy_MPI_Register_datarep_c
#define MPI_File_f2c proxy_MPI_File_f2c
#define MPI_File_c2f proxy_MPI_File_c2f
#define MPI_Address proxy_MPI_Get_address
#define MPI_Errhandler_create proxy_MPI_Comm_create_errhandler
#define MPI_Errhandler_get proxy_MPI_Comm_get_errhandler
#define MPI_Errhandler_set proxy_MPI_Comm_set_errhandler
#define MPI_Type_struct proxy_MPI_Type_create_struct
#define MPI_Type_hvector proxy_MPI_Type_create_hvector
#define MPI_Type_hindexed proxy_MPI_Type_create_hindexed
#define MPI_Type_extent proxy_MPI_Type_create_extent
#define MPI_Type_lb proxy_MPI_Type_create_lb
#define MPI_Type_ub proxy_MPI_Type_create_ub
#endif
#define proxy_MPI_COMM_NULL proxy_MPI_COMM_NULL_CONST()
#define proxy_MPI_OP_NULL proxy_MPI_OP_NULL_CONST()
#define proxy_MPI_GROUP_NULL proxy_MPI_GROUP_NULL_CONST()
#define proxy_MPI_DATATYPE_NULL proxy_MPI_DATATYPE_NULL_CONST()
#define proxy_MPI_REQUEST_NULL proxy_MPI_REQUEST_NULL_CONST()
#define proxy_MPI_ERRHANDLER_NULL proxy_MPI_ERRHANDLER_NULL_CONST()
#define proxy_MPI_IDENT proxy_MPI_IDENT_CONST()
#define proxy_MPI_CONGRUENT proxy_MPI_CONGRUENT_CONST()
#define proxy_MPI_SIMILAR proxy_MPI_SIMILAR_CONST()
#define proxy_MPI_UNEQUAL proxy_MPI_UNEQUAL_CONST()
#define proxy_MPI_CHAR proxy_MPI_CHAR_CONST()
#define proxy_MPI_SIGNED_CHAR proxy_MPI_SIGNED_CHAR_CONST()
#define proxy_MPI_UNSIGNED_CHAR proxy_MPI_UNSIGNED_CHAR_CONST()
#define proxy_MPI_BYTE proxy_MPI_BYTE_CONST()
#define proxy_MPI_WCHAR proxy_MPI_WCHAR_CONST()
#define proxy_MPI_SHORT proxy_MPI_SHORT_CONST()
#define proxy_MPI_UNSIGNED_SHORT proxy_MPI_UNSIGNED_SHORT_CONST()
#define proxy_MPI_INT proxy_MPI_INT_CONST()
#define proxy_MPI_UNSIGNED proxy_MPI_UNSIGNED_CONST()
#define proxy_MPI_LONG proxy_MPI_LONG_CONST()
#define proxy_MPI_UNSIGNED_LONG proxy_MPI_UNSIGNED_LONG_CONST()
#define proxy_MPI_FLOAT proxy_MPI_FLOAT_CONST()
#define proxy_MPI_DOUBLE proxy_MPI_DOUBLE_CONST()
#define proxy_MPI_LONG_DOUBLE proxy_MPI_LONG_DOUBLE_CONST()
#define proxy_MPI_LONG_LONG_INT proxy_MPI_LONG_LONG_INT_CONST()
#define proxy_MPI_UNSIGNED_LONG_LONG proxy_MPI_UNSIGNED_LONG_LONG_CONST()
#define proxy_MPI_LONG_LONG proxy_MPI_LONG_LONG_CONST()
#define proxy_MPI_PACKED proxy_MPI_PACKED_CONST()
#define proxy_MPI_FLOAT_INT proxy_MPI_FLOAT_INT_CONST()
#define proxy_MPI_DOUBLE_INT proxy_MPI_DOUBLE_INT_CONST()
#define proxy_MPI_LONG_INT proxy_MPI_LONG_INT_CONST()
#define proxy_MPI_SHORT_INT proxy_MPI_SHORT_INT_CONST()
#define proxy_MPI_2INT proxy_MPI_2INT_CONST()
#define proxy_MPI_LONG_DOUBLE_INT proxy_MPI_LONG_DOUBLE_INT_CONST()
#define proxy_MPI_COMPLEX proxy_MPI_COMPLEX_CONST()
#define proxy_MPI_DOUBLE_COMPLEX proxy_MPI_DOUBLE_COMPLEX_CONST()
#define proxy_MPI_LOGICAL proxy_MPI_LOGICAL_CONST()
#define proxy_MPI_REAL proxy_MPI_REAL_CONST()
#define proxy_MPI_DOUBLE_PRECISION proxy_MPI_DOUBLE_PRECISION_CONST()
#define proxy_MPI_INTEGER proxy_MPI_INTEGER_CONST()
#define proxy_MPI_2INTEGER proxy_MPI_2INTEGER_CONST()
#define proxy_MPI_2REAL proxy_MPI_2REAL_CONST()
#define proxy_MPI_2DOUBLE_PRECISION proxy_MPI_2DOUBLE_PRECISION_CONST()
#define proxy_MPI_CHARACTER proxy_MPI_CHARACTER_CONST()
#define proxy_MPI_REAL4 proxy_MPI_REAL4_CONST()
#define proxy_MPI_REAL8 proxy_MPI_REAL8_CONST()
#define proxy_MPI_COMPLEX8 proxy_MPI_COMPLEX8_CONST()
#define proxy_MPI_COMPLEX16 proxy_MPI_COMPLEX16_CONST()
#define proxy_MPI_INTEGER1 proxy_MPI_INTEGER1_CONST()
#define proxy_MPI_INTEGER2 proxy_MPI_INTEGER2_CONST()
#define proxy_MPI_INTEGER4 proxy_MPI_INTEGER4_CONST()
#define proxy_MPI_INTEGER8 proxy_MPI_INTEGER8_CONST()
#define proxy_MPI_INT8_T proxy_MPI_INT8_T_CONST()
#define proxy_MPI_INT16_T proxy_MPI_INT16_T_CONST()
#define proxy_MPI_INT32_T proxy_MPI_INT32_T_CONST()
#define proxy_MPI_INT64_T proxy_MPI_INT64_T_CONST()
#define proxy_MPI_UINT8_T proxy_MPI_UINT8_T_CONST()
#define proxy_MPI_UINT16_T proxy_MPI_UINT16_T_CONST()
#define proxy_MPI_UINT32_T proxy_MPI_UINT32_T_CONST()
#define proxy_MPI_UINT64_T proxy_MPI_UINT64_T_CONST()
#define proxy_MPI_C_BOOL proxy_MPI_C_BOOL_CONST()
#define proxy_MPI_C_FLOAT_COMPLEX proxy_MPI_C_FLOAT_COMPLEX_CONST()
#define proxy_MPI_C_COMPLEX proxy_MPI_C_COMPLEX_CONST()
#define proxy_MPI_C_DOUBLE_COMPLEX proxy_MPI_C_DOUBLE_COMPLEX_CONST()
#define proxy_MPI_C_LONG_DOUBLE_COMPLEX proxy_MPI_C_LONG_DOUBLE_COMPLEX_CONST()
#define proxy_MPI_AINT proxy_MPI_AINT_CONST()
#define proxy_MPI_OFFSET proxy_MPI_OFFSET_CONST()
#define proxy_MPI_TYPECLASS_REAL proxy_MPI_TYPECLASS_REAL_CONST()
#define proxy_MPI_TYPECLASS_INTEGER proxy_MPI_TYPECLASS_INTEGER_CONST()
#define proxy_MPI_TYPECLASS_COMPLEX proxy_MPI_TYPECLASS_COMPLEX_CONST()
#define proxy_MPI_COMM_WORLD proxy_MPI_COMM_WORLD_CONST()
#define proxy_MPI_COMM_SELF proxy_MPI_COMM_SELF_CONST()
#define proxy_MPI_GROUP_EMPTY proxy_MPI_GROUP_EMPTY_CONST()
#define proxy_MPI_WIN_NULL proxy_MPI_WIN_NULL_CONST()
#define proxy_MPI_FILE_NULL proxy_MPI_FILE_NULL_CONST()
#define proxy_MPI_MAX proxy_MPI_MAX_CONST()
#define proxy_MPI_MIN proxy_MPI_MIN_CONST()
#define proxy_MPI_SUM proxy_MPI_SUM_CONST()
#define proxy_MPI_PROD proxy_MPI_PROD_CONST()
#define proxy_MPI_LAND proxy_MPI_LAND_CONST()
#define proxy_MPI_BAND proxy_MPI_BAND_CONST()
#define proxy_MPI_LOR proxy_MPI_LOR_CONST()
#define proxy_MPI_BOR proxy_MPI_BOR_CONST()
#define proxy_MPI_LXOR proxy_MPI_LXOR_CONST()
#define proxy_MPI_BXOR proxy_MPI_BXOR_CONST()
#define proxy_MPI_MINLOC proxy_MPI_MINLOC_CONST()
#define proxy_MPI_MAXLOC proxy_MPI_MAXLOC_CONST()
#define proxy_MPI_REPLACE proxy_MPI_REPLACE_CONST()
#define proxy_MPI_TAG_UB proxy_MPI_TAG_UB_CONST()
#define proxy_MPI_HOST proxy_MPI_HOST_CONST()
#define proxy_MPI_IO proxy_MPI_IO_CONST()
#define proxy_MPI_WTIME_IS_GLOBAL proxy_MPI_WTIME_IS_GLOBAL_CONST()
#define proxy_MPI_UNIVERSE_SIZE proxy_MPI_UNIVERSE_SIZE_CONST()
#define proxy_MPI_LASTUSEDCODE proxy_MPI_LASTUSEDCODE_CONST()
#define proxy_MPI_APPNUM proxy_MPI_APPNUM_CONST()
#define proxy_MPI_WIN_BASE proxy_MPI_WIN_BASE_CONST()
#define proxy_MPI_WIN_SIZE proxy_MPI_WIN_SIZE_CONST()
#define proxy_MPI_WIN_DISP_UNIT proxy_MPI_WIN_DISP_UNIT_CONST()
#define proxy_MPI_MAX_PROCESSOR_NAME 256
#define proxy_MPI_MAX_ERROR_STRING proxy_MPI_MAX_ERROR_STRING_CONST()
#define proxy_MPI_MAX_PORT_NAME proxy_MPI_MAX_PORT_NAME_CONST()
#define proxy_MPI_MAX_OBJECT_NAME proxy_MPI_MAX_OBJECT_NAME_CONST()
#define proxy_MPI_UNDEFINED proxy_MPI_UNDEFINED_CONST()
#define proxy_MPI_KEYVAL_INVALID proxy_MPI_KEYVAL_INVALID_CONST()
#define proxy_MPI_BSEND_OVERHEAD proxy_MPI_BSEND_OVERHEAD_CONST()
#define proxy_MPI_BOTTOM proxy_MPI_BOTTOM_CONST()
#define proxy_MPI_PROC_NULL proxy_MPI_PROC_NULL_CONST()
#define proxy_MPI_ANY_SOURCE proxy_MPI_ANY_SOURCE_CONST()
#define proxy_MPI_ROOT proxy_MPI_ROOT_CONST()
#define proxy_MPI_ANY_TAG proxy_MPI_ANY_TAG_CONST()
#define proxy_MPI_LOCK_EXCLUSIVE proxy_MPI_LOCK_EXCLUSIVE_CONST()
#define proxy_MPI_LOCK_SHARED proxy_MPI_LOCK_SHARED_CONST()
#define proxy_MPI_ERRORS_ARE_FATAL proxy_MPI_ERRORS_ARE_FATAL_CONST()
#define proxy_MPI_ERRORS_RETURN proxy_MPI_ERRORS_RETURN_CONST()
#define proxy_MPI_NULL_COPY_FN proxy_MPI_NULL_COPY_FN_CONST()
#define proxy_MPI_NULL_DELETE_FN proxy_MPI_NULL_DELETE_FN_CONST()
#define proxy_MPI_DUP_FN proxy_MPI_DUP_FN_CONST()
#define proxy_MPI_COMM_NULL_COPY_FN proxy_MPI_COMM_NULL_COPY_FN_CONST()
#define proxy_MPI_COMM_NULL_DELETE_FN proxy_MPI_COMM_NULL_DELETE_FN_CONST()
#define proxy_MPI_COMM_DUP_FN proxy_MPI_COMM_DUP_FN_CONST()
#define proxy_MPI_WIN_NULL_COPY_FN proxy_MPI_WIN_NULL_COPY_FN_CONST()
#define proxy_MPI_WIN_NULL_DELETE_FN proxy_MPI_WIN_NULL_DELETE_FN_CONST()
#define proxy_MPI_WIN_DUP_FN proxy_MPI_WIN_DUP_FN_CONST()
#define proxy_MPI_TYPE_NULL_COPY_FN proxy_MPI_TYPE_NULL_COPY_FN_CONST()
#define proxy_MPI_TYPE_NULL_DELETE_FN proxy_MPI_TYPE_NULL_DELETE_FN_CONST()
#define proxy_MPI_TYPE_DUP_FN proxy_MPI_TYPE_DUP_FN_CONST()
#define proxy_MPI_INFO_NULL proxy_MPI_INFO_NULL_CONST()
#define proxy_MPI_MAX_INFO_KEY proxy_MPI_MAX_INFO_KEY_CONST()
#define proxy_MPI_MAX_INFO_VAL proxy_MPI_MAX_INFO_VAL_CONST()
#define proxy_MPI_ORDER_C proxy_MPI_ORDER_C_CONST()
#define proxy_MPI_ORDER_FORTRAN proxy_MPI_ORDER_FORTRAN_CONST()
#define proxy_MPI_DISTRIBUTE_BLOCK proxy_MPI_DISTRIBUTE_BLOCK_CONST()
#define proxy_MPI_DISTRIBUTE_CYCLIC proxy_MPI_DISTRIBUTE_CYCLIC_CONST()
#define proxy_MPI_DISTRIBUTE_NONE proxy_MPI_DISTRIBUTE_NONE_CONST()
#define proxy_MPI_DISTRIBUTE_DFLT_DARG proxy_MPI_DISTRIBUTE_DFLT_DARG_CONST()
#define proxy_MPI_IN_PLACE proxy_MPI_IN_PLACE_CONST()
#define proxy_MPI_MODE_NOCHECK proxy_MPI_MODE_NOCHECK_CONST()
#define proxy_MPI_MODE_NOSTORE proxy_MPI_MODE_NOSTORE_CONST()
#define proxy_MPI_MODE_NOPUT proxy_MPI_MODE_NOPUT_CONST()
#define proxy_MPI_MODE_NOPRECEDE proxy_MPI_MODE_NOPRECEDE_CONST()
#define proxy_MPI_MODE_NOSUCCEED proxy_MPI_MODE_NOSUCCEED_CONST()
#define proxy_MPI_STATUS_IGNORE proxy_MPI_STATUS_IGNORE_CONST()
#define proxy_MPI_STATUSES_IGNORE proxy_MPI_STATUSES_IGNORE_CONST()
#define proxy_MPI_ERRCODES_IGNORE proxy_MPI_ERRCODES_IGNORE_CONST()
#define proxy_MPI_ARGV_NULL proxy_MPI_ARGV_NULL_CONST()
#define proxy_MPI_ARGVS_NULL proxy_MPI_ARGVS_NULL_CONST()
#define proxy_MPI_THREAD_SINGLE proxy_MPI_THREAD_SINGLE_CONST()
#define proxy_MPI_THREAD_FUNNELED proxy_MPI_THREAD_FUNNELED_CONST()
#define proxy_MPI_THREAD_SERIALIZED proxy_MPI_THREAD_SERIALIZED_CONST()
#define proxy_MPI_THREAD_MULTIPLE proxy_MPI_THREAD_MULTIPLE_CONST()
#define proxy_MPI_SUCCESS proxy_MPI_SUCCESS_CONST()
#define proxy_MPI_ERR_BUFFER proxy_MPI_ERR_BUFFER_CONST()
#define proxy_MPI_ERR_COUNT proxy_MPI_ERR_COUNT_CONST()
#define proxy_MPI_ERR_TYPE proxy_MPI_ERR_TYPE_CONST()
#define proxy_MPI_ERR_TAG proxy_MPI_ERR_TAG_CONST()
#define proxy_MPI_ERR_COMM proxy_MPI_ERR_COMM_CONST()
#define proxy_MPI_ERR_RANK proxy_MPI_ERR_RANK_CONST()
#define proxy_MPI_ERR_ROOT proxy_MPI_ERR_ROOT_CONST()
#define proxy_MPI_ERR_TRUNCATE proxy_MPI_ERR_TRUNCATE_CONST()
#define proxy_MPI_ERR_GROUP proxy_MPI_ERR_GROUP_CONST()
#define proxy_MPI_ERR_OP proxy_MPI_ERR_OP_CONST()
#define proxy_MPI_ERR_REQUEST proxy_MPI_ERR_REQUEST_CONST()
#define proxy_MPI_ERR_TOPOLOGY proxy_MPI_ERR_TOPOLOGY_CONST()
#define proxy_MPI_ERR_DIMS proxy_MPI_ERR_DIMS_CONST()
#define proxy_MPI_ERR_ARG proxy_MPI_ERR_ARG_CONST()
#define proxy_MPI_ERR_OTHER proxy_MPI_ERR_OTHER_CONST()
#define proxy_MPI_ERR_UNKNOWN proxy_MPI_ERR_UNKNOWN_CONST()
#define proxy_MPI_ERR_INTERN proxy_MPI_ERR_INTERN_CONST()
#define proxy_MPI_ERR_IN_STATUS proxy_MPI_ERR_IN_STATUS_CONST()
#define proxy_MPI_ERR_PENDING proxy_MPI_ERR_PENDING_CONST()
#define proxy_MPI_ERR_ACCESS proxy_MPI_ERR_ACCESS_CONST()
#define proxy_MPI_ERR_AMODE proxy_MPI_ERR_AMODE_CONST()
#define proxy_MPI_ERR_BAD_FILE proxy_MPI_ERR_BAD_FILE_CONST()
#define proxy_MPI_ERR_CONVERSION proxy_MPI_ERR_CONVERSION_CONST()
#define proxy_MPI_ERR_DUP_DATAREP proxy_MPI_ERR_DUP_DATAREP_CONST()
#define proxy_MPI_ERR_FILE_EXISTS proxy_MPI_ERR_FILE_EXISTS_CONST()
#define proxy_MPI_ERR_FILE_IN_USE proxy_MPI_ERR_FILE_IN_USE_CONST()
#define proxy_MPI_ERR_FILE proxy_MPI_ERR_FILE_CONST()
#define proxy_MPI_ERR_IO proxy_MPI_ERR_IO_CONST()
#define proxy_MPI_ERR_NO_SPACE proxy_MPI_ERR_NO_SPACE_CONST()
#define proxy_MPI_ERR_NO_SUCH_FILE proxy_MPI_ERR_NO_SUCH_FILE_CONST()
#define proxy_MPI_ERR_READ_ONLY proxy_MPI_ERR_READ_ONLY_CONST()
#define proxy_MPI_ERR_UNSUPPORTED_DATAREP proxy_MPI_ERR_UNSUPPORTED_DATAREP_CONST()
#define proxy_MPI_ERR_INFO proxy_MPI_ERR_INFO_CONST()
#define proxy_MPI_ERR_INFO_KEY proxy_MPI_ERR_INFO_KEY_CONST()
#define proxy_MPI_ERR_INFO_VALUE proxy_MPI_ERR_INFO_VALUE_CONST()
#define proxy_MPI_ERR_INFO_NOKEY proxy_MPI_ERR_INFO_NOKEY_CONST()
#define proxy_MPI_ERR_NAME proxy_MPI_ERR_NAME_CONST()
#define proxy_MPI_ERR_NO_MEM proxy_MPI_ERR_NO_MEM_CONST()
#define proxy_MPI_ERR_NOT_SAME proxy_MPI_ERR_NOT_SAME_CONST()
#define proxy_MPI_ERR_PORT proxy_MPI_ERR_PORT_CONST()
#define proxy_MPI_ERR_QUOTA proxy_MPI_ERR_QUOTA_CONST()
#define proxy_MPI_ERR_SERVICE proxy_MPI_ERR_SERVICE_CONST()
#define proxy_MPI_ERR_SPAWN proxy_MPI_ERR_SPAWN_CONST()
#define proxy_MPI_ERR_UNSUPPORTED_OPERATION proxy_MPI_ERR_UNSUPPORTED_OPERATION_CONST()
#define proxy_MPI_ERR_WIN proxy_MPI_ERR_WIN_CONST()
#define proxy_MPI_ERR_BASE proxy_MPI_ERR_BASE_CONST()
#define proxy_MPI_ERR_LOCKTYPE proxy_MPI_ERR_LOCKTYPE_CONST()
#define proxy_MPI_ERR_KEYVAL proxy_MPI_ERR_KEYVAL_CONST()
#define proxy_MPI_ERR_RMA_CONFLICT proxy_MPI_ERR_RMA_CONFLICT_CONST()
#define proxy_MPI_ERR_RMA_SYNC proxy_MPI_ERR_RMA_SYNC_CONST()
#define proxy_MPI_ERR_SIZE proxy_MPI_ERR_SIZE_CONST()
#define proxy_MPI_ERR_DISP proxy_MPI_ERR_DISP_CONST()
#define proxy_MPI_ERR_ASSERT proxy_MPI_ERR_ASSERT_CONST()
#define proxy_MPI_ERR_LASTCODE proxy_MPI_ERR_LASTCODE_CONST()
#define proxy_MPI_CONVERSION_FN_NULL proxy_MPI_CONVERSION_FN_NULL_CONST()
#define proxy_MPI_MODE_RDONLY proxy_MPI_MODE_RDONLY_CONST()
#define proxy_MPI_MODE_RDWR proxy_MPI_MODE_RDWR_CONST()
#define proxy_MPI_MODE_WRONLY proxy_MPI_MODE_WRONLY_CONST()
#define proxy_MPI_MODE_CREATE proxy_MPI_MODE_CREATE_CONST()
#define proxy_MPI_MODE_EXCL proxy_MPI_MODE_EXCL_CONST()
#define proxy_MPI_MODE_DELETE_ON_CLOSE proxy_MPI_MODE_DELETE_ON_CLOSE_CONST()
#define proxy_MPI_MODE_UNIQUE_OPEN proxy_MPI_MODE_UNIQUE_OPEN_CONST()
#define proxy_MPI_MODE_APPEND proxy_MPI_MODE_APPEND_CONST()
#define proxy_MPI_MODE_SEQUENTIAL proxy_MPI_MODE_SEQUENTIAL_CONST()
#define proxy_MPI_DISPLACEMENT_CURRENT proxy_MPI_DISPLACEMENT_CURRENT_CONST()
#define proxy_MPI_SEEK_SET proxy_MPI_SEEK_SET_CONST()
#define proxy_MPI_SEEK_CUR proxy_MPI_SEEK_CUR_CONST()
#define proxy_MPI_SEEK_END proxy_MPI_SEEK_END_CONST()
#define proxy_MPI_MAX_DATAREP_STRING proxy_MPI_MAX_DATAREP_STRING_CONST()
typedef void* proxy_MPI_Datatype;
typedef void* proxy_MPI_Comm;
typedef void* proxy_MPI_Group;
typedef void* proxy_MPI_Win;
typedef void* proxy_MPI_File;
typedef void* proxy_MPI_Op;
typedef void ( proxy_MPI_Handler_function ) ( proxy_MPI_Comm * , int * , ... );
typedef int ( proxy_MPI_Comm_copy_attr_function ) ( proxy_MPI_Comm , int , void * , void * , void * , int * );
typedef int ( proxy_MPI_Comm_delete_attr_function ) ( proxy_MPI_Comm , int , void * , void * );
typedef int ( proxy_MPI_Type_copy_attr_function ) ( proxy_MPI_Datatype , int , void * , void * , void * , int * );
typedef int ( proxy_MPI_Type_delete_attr_function ) ( proxy_MPI_Datatype , int , void * , void * );
typedef int ( proxy_MPI_Win_copy_attr_function ) ( proxy_MPI_Win , int , void * , void * , void * , int * );
typedef int ( proxy_MPI_Win_delete_attr_function ) ( proxy_MPI_Win , int , void * , void * );
typedef void ( proxy_MPI_Comm_errhandler_function ) ( proxy_MPI_Comm * , int * , ... );
typedef void ( proxy_MPI_File_errhandler_function ) ( proxy_MPI_File * , int * , ... );
typedef void ( proxy_MPI_Win_errhandler_function ) ( proxy_MPI_Win * , int * , ... );
typedef proxy_MPI_Comm_errhandler_function proxy_MPI_Comm_errhandler_fn;
typedef proxy_MPI_File_errhandler_function proxy_MPI_File_errhandler_fn;
typedef proxy_MPI_Win_errhandler_function proxy_MPI_Win_errhandler_fn;
typedef void* proxy_MPI_Errhandler;
typedef void* proxy_MPI_Request;
typedef int ( proxy_MPI_Copy_function ) ( proxy_MPI_Comm , int , void * , void * , void * , int * );
typedef int ( proxy_MPI_Delete_function ) ( proxy_MPI_Comm , int , void * , void * );
typedef void* proxy_MPI_Info;
typedef int64_t proxy_MPI_Aint;
typedef int32_t proxy_MPI_Fint;
typedef int64_t proxy_MPI_Offset;
typedef struct proxy_MPI_Status_struct {  int MPI_SOURCE ; int MPI_TAG ; int MPI_ERROR ; int reserved[10]; } proxy_MPI_Status; ;
typedef void ( proxy_MPI_User_function ) ( void * , void * , int * , proxy_MPI_Datatype * );
typedef int ( proxy_MPI_Grequest_cancel_function ) ( void * , int );
typedef int ( proxy_MPI_Grequest_free_function ) ( void * );
typedef int ( proxy_MPI_Grequest_query_function ) ( void * , proxy_MPI_Status * );
typedef int ( proxy_MPI_Datarep_conversion_function ) ( void * , proxy_MPI_Datatype , int , void * , proxy_MPI_Offset , void * );
typedef int ( proxy_MPI_Datarep_extent_function ) ( proxy_MPI_Datatype datatype , proxy_MPI_Aint * , void * );
int proxy_MPI_Status_c2f ( const proxy_MPI_Status * c_status , proxy_MPI_Fint * f_status );
int proxy_MPI_Status_f2c ( const proxy_MPI_Fint * f_status , proxy_MPI_Status * c_status );
int proxy_MPI_Type_create_f90_integer ( int r , proxy_MPI_Datatype * newtype );
int proxy_MPI_Type_create_f90_real ( int p , int r , proxy_MPI_Datatype * newtype );
int proxy_MPI_Type_create_f90_complex ( int p , int r , proxy_MPI_Datatype * newtype );
int proxy_MPI_Attr_delete ( proxy_MPI_Comm comm , int keyval );
int proxy_MPI_Attr_get ( proxy_MPI_Comm comm , int keyval , void * attribute_val , int * flag );
int proxy_MPI_Attr_put ( proxy_MPI_Comm comm , int keyval , void * attribute_val );
int proxy_MPI_Comm_create_keyval ( proxy_MPI_Comm_copy_attr_function * comm_copy_attr_fn , proxy_MPI_Comm_delete_attr_function * comm_delete_attr_fn , int * comm_keyval , void * extra_state );
int proxy_MPI_Comm_delete_attr ( proxy_MPI_Comm comm , int comm_keyval );
int proxy_MPI_Comm_free_keyval ( int * comm_keyval );
int proxy_MPI_Comm_get_attr ( proxy_MPI_Comm comm , int comm_keyval , void * attribute_val , int * flag );
int proxy_MPI_Comm_set_attr ( proxy_MPI_Comm comm , int comm_keyval , void * attribute_val );
int proxy_MPI_Keyval_create ( proxy_MPI_Copy_function * copy_fn , proxy_MPI_Delete_function * delete_fn , int * keyval , void * extra_state );
int proxy_MPI_Keyval_free ( int * keyval );
int proxy_MPI_Type_create_keyval ( proxy_MPI_Type_copy_attr_function * type_copy_attr_fn , proxy_MPI_Type_delete_attr_function * type_delete_attr_fn , int * type_keyval , void * extra_state );
int proxy_MPI_Type_delete_attr ( proxy_MPI_Datatype datatype , int type_keyval );
int proxy_MPI_Type_free_keyval ( int * type_keyval );
int proxy_MPI_Type_get_attr ( proxy_MPI_Datatype datatype , int type_keyval , void * attribute_val , int * flag );
int proxy_MPI_Type_set_attr ( proxy_MPI_Datatype datatype , int type_keyval , void * attribute_val );
int proxy_MPI_Win_create_keyval ( proxy_MPI_Win_copy_attr_function * win_copy_attr_fn , proxy_MPI_Win_delete_attr_function * win_delete_attr_fn , int * win_keyval , void * extra_state );
int proxy_MPI_Win_delete_attr ( proxy_MPI_Win win , int win_keyval );
int proxy_MPI_Win_free_keyval ( int * win_keyval );
int proxy_MPI_Win_get_attr ( proxy_MPI_Win win , int win_keyval , void * attribute_val , int * flag );
int proxy_MPI_Win_set_attr ( proxy_MPI_Win win , int win_keyval , void * attribute_val );
int proxy_MPI_Allgather ( const void * sendbuf , int sendcount , proxy_MPI_Datatype sendtype , void * recvbuf , int recvcount , proxy_MPI_Datatype recvtype , proxy_MPI_Comm comm );
int proxy_MPI_Allgatherv ( const void * sendbuf , int sendcount , proxy_MPI_Datatype sendtype , void * recvbuf , const int recvcounts [ ] , const int displs [ ] , proxy_MPI_Datatype recvtype , proxy_MPI_Comm comm );
int proxy_MPI_Allreduce ( const void * sendbuf , void * recvbuf , int count , proxy_MPI_Datatype datatype , proxy_MPI_Op op , proxy_MPI_Comm comm );
int proxy_MPI_Alltoall ( const void * sendbuf , int sendcount , proxy_MPI_Datatype sendtype , void * recvbuf , int recvcount , proxy_MPI_Datatype recvtype , proxy_MPI_Comm comm );
int proxy_MPI_Alltoallv ( const void * sendbuf , const int sendcounts [ ] , const int sdispls [ ] , proxy_MPI_Datatype sendtype , void * recvbuf , const int recvcounts [ ] , const int rdispls [ ] , proxy_MPI_Datatype recvtype , proxy_MPI_Comm comm );
int proxy_MPI_Alltoallw ( const void * sendbuf , const int sendcounts [ ] , const int sdispls [ ] , const proxy_MPI_Datatype sendtypes [ ] , void * recvbuf , const int recvcounts [ ] , const int rdispls [ ] , const proxy_MPI_Datatype recvtypes [ ] , proxy_MPI_Comm comm );
int proxy_MPI_Barrier ( proxy_MPI_Comm comm );
int proxy_MPI_Bcast ( void * buffer , int count , proxy_MPI_Datatype datatype , int root , proxy_MPI_Comm comm );
int proxy_MPI_Exscan ( const void * sendbuf , void * recvbuf , int count , proxy_MPI_Datatype datatype , proxy_MPI_Op op , proxy_MPI_Comm comm );
int proxy_MPI_Gather ( const void * sendbuf , int sendcount , proxy_MPI_Datatype sendtype , void * recvbuf , int recvcount , proxy_MPI_Datatype recvtype , int root , proxy_MPI_Comm comm );
int proxy_MPI_Gatherv ( const void * sendbuf , int sendcount , proxy_MPI_Datatype sendtype , void * recvbuf , const int recvcounts [ ] , const int displs [ ] , proxy_MPI_Datatype recvtype , int root , proxy_MPI_Comm comm );
int proxy_MPI_Reduce ( const void * sendbuf , void * recvbuf , int count , proxy_MPI_Datatype datatype , proxy_MPI_Op op , int root , proxy_MPI_Comm comm );
int proxy_MPI_Reduce_local ( const void * inbuf , void * inoutbuf , int count , proxy_MPI_Datatype datatype , proxy_MPI_Op op );
int proxy_MPI_Reduce_scatter ( const void * sendbuf , void * recvbuf , const int recvcounts [ ] , proxy_MPI_Datatype datatype , proxy_MPI_Op op , proxy_MPI_Comm comm );
int proxy_MPI_Scan ( const void * sendbuf , void * recvbuf , int count , proxy_MPI_Datatype datatype , proxy_MPI_Op op , proxy_MPI_Comm comm );
int proxy_MPI_Scatter ( const void * sendbuf , int sendcount , proxy_MPI_Datatype sendtype , void * recvbuf , int recvcount , proxy_MPI_Datatype recvtype , int root , proxy_MPI_Comm comm );
int proxy_MPI_Scatterv ( const void * sendbuf , const int sendcounts [ ] , const int displs [ ] , proxy_MPI_Datatype sendtype , void * recvbuf , int recvcount , proxy_MPI_Datatype recvtype , int root , proxy_MPI_Comm comm );
int proxy_MPI_Comm_compare ( proxy_MPI_Comm comm1 , proxy_MPI_Comm comm2 , int * result );
int proxy_MPI_Comm_create ( proxy_MPI_Comm comm , proxy_MPI_Group group , proxy_MPI_Comm * newcomm );
int proxy_MPI_Comm_dup ( proxy_MPI_Comm comm , proxy_MPI_Comm * newcomm );
int proxy_MPI_Comm_free ( proxy_MPI_Comm * comm );
int proxy_MPI_Comm_get_name ( proxy_MPI_Comm comm , char * comm_name , int * resultlen );
int proxy_MPI_Comm_group ( proxy_MPI_Comm comm , proxy_MPI_Group * group );
int proxy_MPI_Comm_rank ( proxy_MPI_Comm comm , int * rank );
int proxy_MPI_Comm_remote_group ( proxy_MPI_Comm comm , proxy_MPI_Group * group );
int proxy_MPI_Comm_remote_size ( proxy_MPI_Comm comm , int * size );
int proxy_MPI_Comm_set_name ( proxy_MPI_Comm comm , const char * comm_name );
int proxy_MPI_Comm_size ( proxy_MPI_Comm comm , int * size );
int proxy_MPI_Comm_split ( proxy_MPI_Comm comm , int color , int key , proxy_MPI_Comm * newcomm );
int proxy_MPI_Comm_test_inter ( proxy_MPI_Comm comm , int * flag );
int proxy_MPI_Intercomm_create ( proxy_MPI_Comm local_comm , int local_leader , proxy_MPI_Comm peer_comm , int remote_leader , int tag , proxy_MPI_Comm * newintercomm );
int proxy_MPI_Intercomm_merge ( proxy_MPI_Comm intercomm , int high , proxy_MPI_Comm * newintracomm );
int proxy_MPI_Get_address ( const void * location , proxy_MPI_Aint * address );
int proxy_MPI_Get_count ( const proxy_MPI_Status * status , proxy_MPI_Datatype datatype , int * count );
int proxy_MPI_Get_elements ( const proxy_MPI_Status * status , proxy_MPI_Datatype datatype , int * count );
int proxy_MPI_Pack ( const void * inbuf , int incount , proxy_MPI_Datatype datatype , void * outbuf , int outsize , int * position , proxy_MPI_Comm comm );
int proxy_MPI_Pack_external ( const char * datarep , const void * inbuf , int incount , proxy_MPI_Datatype datatype , void * outbuf , proxy_MPI_Aint outsize , proxy_MPI_Aint * position );
int proxy_MPI_Pack_external_size ( const char * datarep , int incount , proxy_MPI_Datatype datatype , proxy_MPI_Aint * size );
int proxy_MPI_Pack_size ( int incount , proxy_MPI_Datatype datatype , proxy_MPI_Comm comm , int * size );
int proxy_MPI_Status_set_elements ( proxy_MPI_Status * status , proxy_MPI_Datatype datatype , int count );
int proxy_MPI_Type_commit ( proxy_MPI_Datatype * datatype );
int proxy_MPI_Type_contiguous ( int count , proxy_MPI_Datatype oldtype , proxy_MPI_Datatype * newtype );
int proxy_MPI_Type_create_darray ( int size , int rank , int ndims , const int array_of_gsizes [ ] , const int array_of_distribs [ ] , const int array_of_dargs [ ] , const int array_of_psizes [ ] , int order , proxy_MPI_Datatype oldtype , proxy_MPI_Datatype * newtype );
int proxy_MPI_Type_create_hindexed ( int count , const int array_of_blocklengths [ ] , const proxy_MPI_Aint array_of_displacements [ ] , proxy_MPI_Datatype oldtype , proxy_MPI_Datatype * newtype );
int proxy_MPI_Type_create_hvector ( int count , int blocklength , proxy_MPI_Aint stride , proxy_MPI_Datatype oldtype , proxy_MPI_Datatype * newtype );
int proxy_MPI_Type_create_indexed_block ( int count , int blocklength , const int array_of_displacements [ ] , proxy_MPI_Datatype oldtype , proxy_MPI_Datatype * newtype );
int proxy_MPI_Type_create_resized ( proxy_MPI_Datatype oldtype , proxy_MPI_Aint lb , proxy_MPI_Aint extent , proxy_MPI_Datatype * newtype );
int proxy_MPI_Type_create_struct ( int count , const int array_of_blocklengths [ ] , const proxy_MPI_Aint array_of_displacements [ ] , const proxy_MPI_Datatype array_of_types [ ] , proxy_MPI_Datatype * newtype );
int proxy_MPI_Type_create_subarray ( int ndims , const int array_of_sizes [ ] , const int array_of_subsizes [ ] , const int array_of_starts [ ] , int order , proxy_MPI_Datatype oldtype , proxy_MPI_Datatype * newtype );
int proxy_MPI_Type_dup ( proxy_MPI_Datatype oldtype , proxy_MPI_Datatype * newtype );
int proxy_MPI_Type_free ( proxy_MPI_Datatype * datatype );
int proxy_MPI_Type_get_contents ( proxy_MPI_Datatype datatype , int max_integers , int max_addresses , int max_datatypes , int array_of_integers [ ] , proxy_MPI_Aint array_of_addresses [ ] , proxy_MPI_Datatype array_of_datatypes [ ] );
int proxy_MPI_Type_get_envelope ( proxy_MPI_Datatype datatype , int * num_integers , int * num_addresses , int * num_datatypes , int * combiner );
int proxy_MPI_Type_get_extent ( proxy_MPI_Datatype datatype , proxy_MPI_Aint * lb , proxy_MPI_Aint * extent );
int proxy_MPI_Type_get_name ( proxy_MPI_Datatype datatype , char * type_name , int * resultlen );
int proxy_MPI_Type_get_true_extent ( proxy_MPI_Datatype datatype , proxy_MPI_Aint * true_lb , proxy_MPI_Aint * true_extent );
int proxy_MPI_Type_indexed ( int count , const int array_of_blocklengths [ ] , const int array_of_displacements [ ] , proxy_MPI_Datatype oldtype , proxy_MPI_Datatype * newtype );
int proxy_MPI_Type_match_size ( int typeclass , int size , proxy_MPI_Datatype * datatype );
int proxy_MPI_Type_set_name ( proxy_MPI_Datatype datatype , const char * type_name );
int proxy_MPI_Type_size ( proxy_MPI_Datatype datatype , int * size );
int proxy_MPI_Type_vector ( int count , int blocklength , int stride , proxy_MPI_Datatype oldtype , proxy_MPI_Datatype * newtype );
int proxy_MPI_Unpack ( const void * inbuf , int insize , int * position , void * outbuf , int outcount , proxy_MPI_Datatype datatype , proxy_MPI_Comm comm );
int proxy_MPI_Unpack_external ( const char datarep [ ] , const void * inbuf , proxy_MPI_Aint insize , proxy_MPI_Aint * position , void * outbuf , int outcount , proxy_MPI_Datatype datatype );
int proxy_MPI_Add_error_class ( int * errorclass );
int proxy_MPI_Add_error_code ( int errorclass , int * errorcode );
int proxy_MPI_Add_error_string ( int errorcode , const char * string );
int proxy_MPI_Comm_call_errhandler ( proxy_MPI_Comm comm , int errorcode );
int proxy_MPI_Comm_create_errhandler ( proxy_MPI_Comm_errhandler_function * comm_errhandler_fn , proxy_MPI_Errhandler * errhandler );
int proxy_MPI_Comm_get_errhandler ( proxy_MPI_Comm comm , proxy_MPI_Errhandler * errhandler );
int proxy_MPI_Comm_set_errhandler ( proxy_MPI_Comm comm , proxy_MPI_Errhandler errhandler );
int proxy_MPI_Errhandler_free ( proxy_MPI_Errhandler * errhandler );
int proxy_MPI_Error_class ( int errorcode , int * errorclass );
int proxy_MPI_Error_string ( int errorcode , char * string , int * resultlen );
int proxy_MPI_File_call_errhandler ( proxy_MPI_File fh , int errorcode );
int proxy_MPI_File_create_errhandler ( proxy_MPI_File_errhandler_function * file_errhandler_fn , proxy_MPI_Errhandler * errhandler );
int proxy_MPI_File_get_errhandler ( proxy_MPI_File file , proxy_MPI_Errhandler * errhandler );
int proxy_MPI_File_set_errhandler ( proxy_MPI_File file , proxy_MPI_Errhandler errhandler );
int proxy_MPI_Win_call_errhandler ( proxy_MPI_Win win , int errorcode );
int proxy_MPI_Win_create_errhandler ( proxy_MPI_Win_errhandler_function * win_errhandler_fn , proxy_MPI_Errhandler * errhandler );
int proxy_MPI_Win_get_errhandler ( proxy_MPI_Win win , proxy_MPI_Errhandler * errhandler );
int proxy_MPI_Win_set_errhandler ( proxy_MPI_Win win , proxy_MPI_Errhandler errhandler );
int proxy_MPI_Group_compare ( proxy_MPI_Group group1 , proxy_MPI_Group group2 , int * result );
int proxy_MPI_Group_difference ( proxy_MPI_Group group1 , proxy_MPI_Group group2 , proxy_MPI_Group * newgroup );
int proxy_MPI_Group_excl ( proxy_MPI_Group group , int n , const int ranks [ ] , proxy_MPI_Group * newgroup );
int proxy_MPI_Group_free ( proxy_MPI_Group * group );
int proxy_MPI_Group_incl ( proxy_MPI_Group group , int n , const int ranks [ ] , proxy_MPI_Group * newgroup );
int proxy_MPI_Group_intersection ( proxy_MPI_Group group1 , proxy_MPI_Group group2 , proxy_MPI_Group * newgroup );
int proxy_MPI_Group_range_excl ( proxy_MPI_Group group , int n , int ranges [ ] [ 3 ] , proxy_MPI_Group * newgroup );
int proxy_MPI_Group_range_incl ( proxy_MPI_Group group , int n , int ranges [ ] [ 3 ] , proxy_MPI_Group * newgroup );
int proxy_MPI_Group_rank ( proxy_MPI_Group group , int * rank );
int proxy_MPI_Group_size ( proxy_MPI_Group group , int * size );
int proxy_MPI_Group_translate_ranks ( proxy_MPI_Group group1 , int n , const int ranks1 [ ] , proxy_MPI_Group group2 , int ranks2 [ ] );
int proxy_MPI_Group_union ( proxy_MPI_Group group1 , proxy_MPI_Group group2 , proxy_MPI_Group * newgroup );
int proxy_MPI_Info_create ( proxy_MPI_Info * info );
int proxy_MPI_Info_delete ( proxy_MPI_Info info , const char * key );
int proxy_MPI_Info_dup ( proxy_MPI_Info info , proxy_MPI_Info * newinfo );
int proxy_MPI_Info_free ( proxy_MPI_Info * info );
int proxy_MPI_Info_get ( proxy_MPI_Info info , const char * key , int valuelen , char * value , int * flag );
int proxy_MPI_Info_get_nkeys ( proxy_MPI_Info info , int * nkeys );
int proxy_MPI_Info_get_nthkey ( proxy_MPI_Info info , int n , char * key );
int proxy_MPI_Info_get_valuelen ( proxy_MPI_Info info , const char * key , int * valuelen , int * flag );
int proxy_MPI_Info_set ( proxy_MPI_Info info , const char * key , const char * value );
int proxy_MPI_Abort ( proxy_MPI_Comm comm , int errorcode );
int proxy_MPI_Finalize ( void );
int proxy_MPI_Finalized ( int * flag );
int proxy_MPI_Init ( int * argc , char * * * argv );
int proxy_MPI_Init_thread ( int * argc , char * * * argv , int required , int * provided );
int proxy_MPI_Initialized ( int * flag );
int proxy_MPI_Is_thread_main ( int * flag );
int proxy_MPI_Query_thread ( int * provided );
int proxy_MPI_Get_processor_name ( char * name , int * resultlen );
int proxy_MPI_Get_version ( int * version , int * subversion );
int proxy_MPI_Pcontrol ( const int level , ... );
int proxy_MPI_Op_commutative ( proxy_MPI_Op op , int * commute );
int proxy_MPI_Op_create ( proxy_MPI_User_function * user_fn , int commute , proxy_MPI_Op * op );
int proxy_MPI_Op_free ( proxy_MPI_Op * op );
int proxy_MPI_Bsend ( const void * buf , int count , proxy_MPI_Datatype datatype , int dest , int tag , proxy_MPI_Comm comm );
int proxy_MPI_Bsend_init ( const void * buf , int count , proxy_MPI_Datatype datatype , int dest , int tag , proxy_MPI_Comm comm , proxy_MPI_Request * request );
int proxy_MPI_Buffer_attach ( void * buffer , int size );
int proxy_MPI_Buffer_detach ( void * buffer_addr , int * size );
int proxy_MPI_Ibsend ( const void * buf , int count , proxy_MPI_Datatype datatype , int dest , int tag , proxy_MPI_Comm comm , proxy_MPI_Request * request );
int proxy_MPI_Iprobe ( int source , int tag , proxy_MPI_Comm comm , int * flag , proxy_MPI_Status * status );
int proxy_MPI_Irecv ( void * buf , int count , proxy_MPI_Datatype datatype , int source , int tag , proxy_MPI_Comm comm , proxy_MPI_Request * request );
int proxy_MPI_Irsend ( const void * buf , int count , proxy_MPI_Datatype datatype , int dest , int tag , proxy_MPI_Comm comm , proxy_MPI_Request * request );
int proxy_MPI_Isend ( const void * buf , int count , proxy_MPI_Datatype datatype , int dest , int tag , proxy_MPI_Comm comm , proxy_MPI_Request * request );
int proxy_MPI_Issend ( const void * buf , int count , proxy_MPI_Datatype datatype , int dest , int tag , proxy_MPI_Comm comm , proxy_MPI_Request * request );
int proxy_MPI_Probe ( int source , int tag , proxy_MPI_Comm comm , proxy_MPI_Status * status );
int proxy_MPI_Recv ( void * buf , int count , proxy_MPI_Datatype datatype , int source , int tag , proxy_MPI_Comm comm , proxy_MPI_Status * status );
int proxy_MPI_Recv_init ( void * buf , int count , proxy_MPI_Datatype datatype , int source , int tag , proxy_MPI_Comm comm , proxy_MPI_Request * request );
int proxy_MPI_Rsend ( const void * buf , int count , proxy_MPI_Datatype datatype , int dest , int tag , proxy_MPI_Comm comm );
int proxy_MPI_Rsend_init ( const void * buf , int count , proxy_MPI_Datatype datatype , int dest , int tag , proxy_MPI_Comm comm , proxy_MPI_Request * request );
int proxy_MPI_Send ( const void * buf , int count , proxy_MPI_Datatype datatype , int dest , int tag , proxy_MPI_Comm comm );
int proxy_MPI_Send_init ( const void * buf , int count , proxy_MPI_Datatype datatype , int dest , int tag , proxy_MPI_Comm comm , proxy_MPI_Request * request );
int proxy_MPI_Sendrecv ( const void * sendbuf , int sendcount , proxy_MPI_Datatype sendtype , int dest , int sendtag , void * recvbuf , int recvcount , proxy_MPI_Datatype recvtype , int source , int recvtag , proxy_MPI_Comm comm , proxy_MPI_Status * status );
int proxy_MPI_Sendrecv_replace ( void * buf , int count , proxy_MPI_Datatype datatype , int dest , int sendtag , int source , int recvtag , proxy_MPI_Comm comm , proxy_MPI_Status * status );
int proxy_MPI_Ssend ( const void * buf , int count , proxy_MPI_Datatype datatype , int dest , int tag , proxy_MPI_Comm comm );
int proxy_MPI_Ssend_init ( const void * buf , int count , proxy_MPI_Datatype datatype , int dest , int tag , proxy_MPI_Comm comm , proxy_MPI_Request * request );
int proxy_MPI_Cancel ( proxy_MPI_Request * request );
int proxy_MPI_Grequest_complete ( proxy_MPI_Request request );
int proxy_MPI_Grequest_start ( proxy_MPI_Grequest_query_function * query_fn , proxy_MPI_Grequest_free_function * free_fn , proxy_MPI_Grequest_cancel_function * cancel_fn , void * extra_state , proxy_MPI_Request * request );
int proxy_MPI_Request_free ( proxy_MPI_Request * request );
int proxy_MPI_Request_get_status ( proxy_MPI_Request request , int * flag , proxy_MPI_Status * status );
int proxy_MPI_Start ( proxy_MPI_Request * request );
int proxy_MPI_Startall ( int count , proxy_MPI_Request array_of_requests [ ] );
int proxy_MPI_Status_set_cancelled ( proxy_MPI_Status * status , int flag );
int proxy_MPI_Test ( proxy_MPI_Request * request , int * flag , proxy_MPI_Status * status );
int proxy_MPI_Test_cancelled ( const proxy_MPI_Status * status , int * flag );
int proxy_MPI_Testall ( int count , proxy_MPI_Request array_of_requests [ ] , int * flag , proxy_MPI_Status array_of_statuses [ ] );
int proxy_MPI_Testany ( int count , proxy_MPI_Request array_of_requests [ ] , int * indx , int * flag , proxy_MPI_Status * status );
int proxy_MPI_Testsome ( int incount , proxy_MPI_Request array_of_requests [ ] , int * outcount , int array_of_indices [ ] , proxy_MPI_Status array_of_statuses [ ] );
int proxy_MPI_Wait ( proxy_MPI_Request * request , proxy_MPI_Status * status );
int proxy_MPI_Waitall ( int count , proxy_MPI_Request array_of_requests [ ] , proxy_MPI_Status array_of_statuses [ ] );
int proxy_MPI_Waitany ( int count , proxy_MPI_Request array_of_requests [ ] , int * indx , proxy_MPI_Status * status );
int proxy_MPI_Waitsome ( int incount , proxy_MPI_Request array_of_requests [ ] , int * outcount , int array_of_indices [ ] , proxy_MPI_Status array_of_statuses [ ] );
int proxy_MPI_Accumulate ( const void * origin_addr , int origin_count , proxy_MPI_Datatype origin_datatype , int target_rank , proxy_MPI_Aint target_disp , int target_count , proxy_MPI_Datatype target_datatype , proxy_MPI_Op op , proxy_MPI_Win win );
int proxy_MPI_Alloc_mem ( proxy_MPI_Aint size , proxy_MPI_Info info , void * baseptr );
int proxy_MPI_Free_mem ( void * base );
int proxy_MPI_Get ( void * origin_addr , int origin_count , proxy_MPI_Datatype origin_datatype , int target_rank , proxy_MPI_Aint target_disp , int target_count , proxy_MPI_Datatype target_datatype , proxy_MPI_Win win );
int proxy_MPI_Put ( const void * origin_addr , int origin_count , proxy_MPI_Datatype origin_datatype , int target_rank , proxy_MPI_Aint target_disp , int target_count , proxy_MPI_Datatype target_datatype , proxy_MPI_Win win );
int proxy_MPI_Win_complete ( proxy_MPI_Win win );
int proxy_MPI_Win_create ( void * base , proxy_MPI_Aint size , int disp_unit , proxy_MPI_Info info , proxy_MPI_Comm comm , proxy_MPI_Win * win );
int proxy_MPI_Win_fence ( int assert , proxy_MPI_Win win );
int proxy_MPI_Win_free ( proxy_MPI_Win * win );
int proxy_MPI_Win_get_group ( proxy_MPI_Win win , proxy_MPI_Group * group );
int proxy_MPI_Win_get_name ( proxy_MPI_Win win , char * win_name , int * resultlen );
int proxy_MPI_Win_lock ( int lock_type , int rank , int assert , proxy_MPI_Win win );
int proxy_MPI_Win_post ( proxy_MPI_Group group , int assert , proxy_MPI_Win win );
int proxy_MPI_Win_set_name ( proxy_MPI_Win win , const char * win_name );
int proxy_MPI_Win_start ( proxy_MPI_Group group , int assert , proxy_MPI_Win win );
int proxy_MPI_Win_test ( proxy_MPI_Win win , int * flag );
int proxy_MPI_Win_unlock ( int rank , proxy_MPI_Win win );
int proxy_MPI_Win_wait ( proxy_MPI_Win win );
int proxy_MPI_Close_port ( const char * port_name );
int proxy_MPI_Comm_accept ( const char * port_name , proxy_MPI_Info info , int root , proxy_MPI_Comm comm , proxy_MPI_Comm * newcomm );
int proxy_MPI_Comm_connect ( const char * port_name , proxy_MPI_Info info , int root , proxy_MPI_Comm comm , proxy_MPI_Comm * newcomm );
int proxy_MPI_Comm_disconnect ( proxy_MPI_Comm * comm );
int proxy_MPI_Comm_get_parent ( proxy_MPI_Comm * parent );
int proxy_MPI_Comm_join ( int fd , proxy_MPI_Comm * intercomm );
int proxy_MPI_Comm_spawn ( const char * command , char * argv [ ] , int maxprocs , proxy_MPI_Info info , int root , proxy_MPI_Comm comm , proxy_MPI_Comm * intercomm , int array_of_errcodes [ ] );
int proxy_MPI_Comm_spawn_multiple ( int count , char * array_of_commands [ ] , char * * array_of_argv [ ] , const int array_of_maxprocs [ ] , const proxy_MPI_Info array_of_info [ ] , int root , proxy_MPI_Comm comm , proxy_MPI_Comm * intercomm , int array_of_errcodes [ ] );
int proxy_MPI_Lookup_name ( const char * service_name , proxy_MPI_Info info , char * port_name );
int proxy_MPI_Open_port ( proxy_MPI_Info info , char * port_name );
int proxy_MPI_Publish_name ( const char * service_name , proxy_MPI_Info info , const char * port_name );
int proxy_MPI_Unpublish_name ( const char * service_name , proxy_MPI_Info info , const char * port_name );
double proxy_MPI_Wtick ( void );
double proxy_MPI_Wtime ( void );
int proxy_MPI_Cart_coords ( proxy_MPI_Comm comm , int rank , int maxdims , int coords [ ] );
int proxy_MPI_Cart_create ( proxy_MPI_Comm comm_old , int ndims , const int dims [ ] , const int periods [ ] , int reorder , proxy_MPI_Comm * comm_cart );
int proxy_MPI_Cart_get ( proxy_MPI_Comm comm , int maxdims , int dims [ ] , int periods [ ] , int coords [ ] );
int proxy_MPI_Cart_map ( proxy_MPI_Comm comm , int ndims , const int dims [ ] , const int periods [ ] , int * newrank );
int proxy_MPI_Cart_rank ( proxy_MPI_Comm comm , const int coords [ ] , int * rank );
int proxy_MPI_Cart_shift ( proxy_MPI_Comm comm , int direction , int disp , int * rank_source , int * rank_dest );
int proxy_MPI_Cart_sub ( proxy_MPI_Comm comm , const int remain_dims [ ] , proxy_MPI_Comm * newcomm );
int proxy_MPI_Cartdim_get ( proxy_MPI_Comm comm , int * ndims );
int proxy_MPI_Dims_create ( int nnodes , int ndims , int dims [ ] );
int proxy_MPI_Graph_create ( proxy_MPI_Comm comm_old , int nnodes , const int indx [ ] , const int edges [ ] , int reorder , proxy_MPI_Comm * comm_graph );
int proxy_MPI_Graph_get ( proxy_MPI_Comm comm , int maxindex , int maxedges , int indx [ ] , int edges [ ] );
int proxy_MPI_Graph_map ( proxy_MPI_Comm comm , int nnodes , const int indx [ ] , const int edges [ ] , int * newrank );
int proxy_MPI_Graph_neighbors ( proxy_MPI_Comm comm , int rank , int maxneighbors , int neighbors [ ] );
int proxy_MPI_Graph_neighbors_count ( proxy_MPI_Comm comm , int rank , int * nneighbors );
int proxy_MPI_Graphdims_get ( proxy_MPI_Comm comm , int * nnodes , int * nedges );
int proxy_MPI_Topo_test ( proxy_MPI_Comm comm , int * status );
int proxy_MPI_File_open ( proxy_MPI_Comm comm , const char * filename , int amode , proxy_MPI_Info info , proxy_MPI_File * fh );
int proxy_MPI_File_close ( proxy_MPI_File * fh );
int proxy_MPI_File_delete ( const char * filename , proxy_MPI_Info info );
int proxy_MPI_File_set_size ( proxy_MPI_File fh , proxy_MPI_Offset size );
int proxy_MPI_File_preallocate ( proxy_MPI_File fh , proxy_MPI_Offset size );
int proxy_MPI_File_get_size ( proxy_MPI_File fh , proxy_MPI_Offset * size );
int proxy_MPI_File_get_group ( proxy_MPI_File fh , proxy_MPI_Group * group );
int proxy_MPI_File_get_amode ( proxy_MPI_File fh , int * amode );
int proxy_MPI_File_set_info ( proxy_MPI_File fh , proxy_MPI_Info info );
int proxy_MPI_File_get_info ( proxy_MPI_File fh , proxy_MPI_Info * info_used );
int proxy_MPI_File_set_view ( proxy_MPI_File fh , proxy_MPI_Offset disp , proxy_MPI_Datatype etype , proxy_MPI_Datatype filetype , const char * datarep , proxy_MPI_Info info );
int proxy_MPI_File_get_view ( proxy_MPI_File fh , proxy_MPI_Offset * disp , proxy_MPI_Datatype * etype , proxy_MPI_Datatype * filetype , char * datarep );
int proxy_MPI_File_read_at ( proxy_MPI_File fh , proxy_MPI_Offset offset , void * buf , int count , proxy_MPI_Datatype datatype , proxy_MPI_Status * status );
int proxy_MPI_File_read_at_all ( proxy_MPI_File fh , proxy_MPI_Offset offset , void * buf , int count , proxy_MPI_Datatype datatype , proxy_MPI_Status * status );
int proxy_MPI_File_write_at ( proxy_MPI_File fh , proxy_MPI_Offset offset , const void * buf , int count , proxy_MPI_Datatype datatype , proxy_MPI_Status * status );
int proxy_MPI_File_write_at_all ( proxy_MPI_File fh , proxy_MPI_Offset offset , const void * buf , int count , proxy_MPI_Datatype datatype , proxy_MPI_Status * status );
int proxy_MPI_File_read ( proxy_MPI_File fh , void * buf , int count , proxy_MPI_Datatype datatype , proxy_MPI_Status * status );
int proxy_MPI_File_read_all ( proxy_MPI_File fh , void * buf , int count , proxy_MPI_Datatype datatype , proxy_MPI_Status * status );
int proxy_MPI_File_write ( proxy_MPI_File fh , const void * buf , int count , proxy_MPI_Datatype datatype , proxy_MPI_Status * status );
int proxy_MPI_File_write_all ( proxy_MPI_File fh , const void * buf , int count , proxy_MPI_Datatype datatype , proxy_MPI_Status * status );
int proxy_MPI_File_seek ( proxy_MPI_File fh , proxy_MPI_Offset offset , int whence );
int proxy_MPI_File_get_position ( proxy_MPI_File fh , proxy_MPI_Offset * offset );
int proxy_MPI_File_get_byte_offset ( proxy_MPI_File fh , proxy_MPI_Offset offset , proxy_MPI_Offset * disp );
int proxy_MPI_File_read_shared ( proxy_MPI_File fh , void * buf , int count , proxy_MPI_Datatype datatype , proxy_MPI_Status * status );
int proxy_MPI_File_write_shared ( proxy_MPI_File fh , const void * buf , int count , proxy_MPI_Datatype datatype , proxy_MPI_Status * status );
int proxy_MPI_File_read_ordered ( proxy_MPI_File fh , void * buf , int count , proxy_MPI_Datatype datatype , proxy_MPI_Status * status );
int proxy_MPI_File_write_ordered ( proxy_MPI_File fh , const void * buf , int count , proxy_MPI_Datatype datatype , proxy_MPI_Status * status );
int proxy_MPI_File_seek_shared ( proxy_MPI_File fh , proxy_MPI_Offset offset , int whence );
int proxy_MPI_File_get_position_shared ( proxy_MPI_File fh , proxy_MPI_Offset * offset );
int proxy_MPI_File_read_at_all_begin ( proxy_MPI_File fh , proxy_MPI_Offset offset , void * buf , int count , proxy_MPI_Datatype datatype );
int proxy_MPI_File_read_at_all_end ( proxy_MPI_File fh , void * buf , proxy_MPI_Status * status );
int proxy_MPI_File_write_at_all_begin ( proxy_MPI_File fh , proxy_MPI_Offset offset , const void * buf , int count , proxy_MPI_Datatype datatype );
int proxy_MPI_File_write_at_all_end ( proxy_MPI_File fh , const void * buf , proxy_MPI_Status * status );
int proxy_MPI_File_read_all_begin ( proxy_MPI_File fh , void * buf , int count , proxy_MPI_Datatype datatype );
int proxy_MPI_File_read_all_end ( proxy_MPI_File fh , void * buf , proxy_MPI_Status * status );
int proxy_MPI_File_write_all_begin ( proxy_MPI_File fh , const void * buf , int count , proxy_MPI_Datatype datatype );
int proxy_MPI_File_write_all_end ( proxy_MPI_File fh , const void * buf , proxy_MPI_Status * status );
int proxy_MPI_File_read_ordered_begin ( proxy_MPI_File fh , void * buf , int count , proxy_MPI_Datatype datatype );
int proxy_MPI_File_read_ordered_end ( proxy_MPI_File fh , void * buf , proxy_MPI_Status * status );
int proxy_MPI_File_write_ordered_begin ( proxy_MPI_File fh , const void * buf , int count , proxy_MPI_Datatype datatype );
int proxy_MPI_File_write_ordered_end ( proxy_MPI_File fh , const void * buf , proxy_MPI_Status * status );
int proxy_MPI_File_get_type_extent ( proxy_MPI_File fh , proxy_MPI_Datatype datatype , proxy_MPI_Aint * extent );
int proxy_MPI_Register_datarep ( const char * datarep , proxy_MPI_Datarep_conversion_function * read_conversion_fn , proxy_MPI_Datarep_conversion_function * write_conversion_fn , proxy_MPI_Datarep_extent_function * dtype_file_extent_fn , void * extra_state );
int proxy_MPI_File_set_atomicity ( proxy_MPI_File fh , int flag );
int proxy_MPI_File_get_atomicity ( proxy_MPI_File fh , int * flag );
int proxy_MPI_File_sync ( proxy_MPI_File fh );
proxy_MPI_File proxy_MPI_File_f2c ( proxy_MPI_Fint file );
proxy_MPI_Fint proxy_MPI_File_c2f ( proxy_MPI_File file );
proxy_MPI_Comm proxy_MPI_COMM_NULL_CONST();
void* proxy_MPI_OP_NULL_CONST();
void* proxy_MPI_GROUP_NULL_CONST();
proxy_MPI_Datatype proxy_MPI_DATATYPE_NULL_CONST();
proxy_MPI_Request proxy_MPI_REQUEST_NULL_CONST();
proxy_MPI_Errhandler proxy_MPI_ERRHANDLER_NULL_CONST();
int64_t proxy_MPI_IDENT_CONST();
int64_t proxy_MPI_CONGRUENT_CONST();
void* proxy_MPI_SIMILAR_CONST();
void* proxy_MPI_UNEQUAL_CONST();
proxy_MPI_Datatype proxy_MPI_CHAR_CONST();
proxy_MPI_Datatype proxy_MPI_SIGNED_CHAR_CONST();
proxy_MPI_Datatype proxy_MPI_UNSIGNED_CHAR_CONST();
proxy_MPI_Datatype proxy_MPI_BYTE_CONST();
proxy_MPI_Datatype proxy_MPI_WCHAR_CONST();
proxy_MPI_Datatype proxy_MPI_SHORT_CONST();
proxy_MPI_Datatype proxy_MPI_UNSIGNED_SHORT_CONST();
proxy_MPI_Datatype proxy_MPI_INT_CONST();
proxy_MPI_Datatype proxy_MPI_UNSIGNED_CONST();
proxy_MPI_Datatype proxy_MPI_LONG_CONST();
proxy_MPI_Datatype proxy_MPI_UNSIGNED_LONG_CONST();
proxy_MPI_Datatype proxy_MPI_FLOAT_CONST();
proxy_MPI_Datatype proxy_MPI_DOUBLE_CONST();
proxy_MPI_Datatype proxy_MPI_LONG_DOUBLE_CONST();
proxy_MPI_Datatype proxy_MPI_LONG_LONG_INT_CONST();
proxy_MPI_Datatype proxy_MPI_UNSIGNED_LONG_LONG_CONST();
proxy_MPI_Datatype proxy_MPI_LONG_LONG_CONST();
proxy_MPI_Datatype proxy_MPI_PACKED_CONST();
proxy_MPI_Datatype proxy_MPI_FLOAT_INT_CONST();
proxy_MPI_Datatype proxy_MPI_DOUBLE_INT_CONST();
proxy_MPI_Datatype proxy_MPI_LONG_INT_CONST();
proxy_MPI_Datatype proxy_MPI_SHORT_INT_CONST();
proxy_MPI_Datatype proxy_MPI_2INT_CONST();
proxy_MPI_Datatype proxy_MPI_LONG_DOUBLE_INT_CONST();
proxy_MPI_Datatype proxy_MPI_COMPLEX_CONST();
proxy_MPI_Datatype proxy_MPI_DOUBLE_COMPLEX_CONST();
proxy_MPI_Datatype proxy_MPI_LOGICAL_CONST();
proxy_MPI_Datatype proxy_MPI_REAL_CONST();
proxy_MPI_Datatype proxy_MPI_DOUBLE_PRECISION_CONST();
proxy_MPI_Datatype proxy_MPI_INTEGER_CONST();
proxy_MPI_Datatype proxy_MPI_2INTEGER_CONST();
proxy_MPI_Datatype proxy_MPI_2REAL_CONST();
proxy_MPI_Datatype proxy_MPI_2DOUBLE_PRECISION_CONST();
proxy_MPI_Datatype proxy_MPI_CHARACTER_CONST();
proxy_MPI_Datatype proxy_MPI_REAL4_CONST();
proxy_MPI_Datatype proxy_MPI_REAL8_CONST();
proxy_MPI_Datatype proxy_MPI_COMPLEX8_CONST();
proxy_MPI_Datatype proxy_MPI_COMPLEX16_CONST();
proxy_MPI_Datatype proxy_MPI_INTEGER1_CONST();
proxy_MPI_Datatype proxy_MPI_INTEGER2_CONST();
proxy_MPI_Datatype proxy_MPI_INTEGER4_CONST();
proxy_MPI_Datatype proxy_MPI_INTEGER8_CONST();
proxy_MPI_Datatype proxy_MPI_INT8_T_CONST();
proxy_MPI_Datatype proxy_MPI_INT16_T_CONST();
proxy_MPI_Datatype proxy_MPI_INT32_T_CONST();
proxy_MPI_Datatype proxy_MPI_INT64_T_CONST();
proxy_MPI_Datatype proxy_MPI_UINT8_T_CONST();
proxy_MPI_Datatype proxy_MPI_UINT16_T_CONST();
proxy_MPI_Datatype proxy_MPI_UINT32_T_CONST();
proxy_MPI_Datatype proxy_MPI_UINT64_T_CONST();
proxy_MPI_Datatype proxy_MPI_C_BOOL_CONST();
proxy_MPI_Datatype proxy_MPI_C_FLOAT_COMPLEX_CONST();
proxy_MPI_Datatype proxy_MPI_C_COMPLEX_CONST();
proxy_MPI_Datatype proxy_MPI_C_DOUBLE_COMPLEX_CONST();
proxy_MPI_Datatype proxy_MPI_C_LONG_DOUBLE_COMPLEX_CONST();
void* proxy_MPI_AINT_CONST();
void* proxy_MPI_OFFSET_CONST();
void* proxy_MPI_TYPECLASS_REAL_CONST();
void* proxy_MPI_TYPECLASS_INTEGER_CONST();
void* proxy_MPI_TYPECLASS_COMPLEX_CONST();
proxy_MPI_Comm proxy_MPI_COMM_WORLD_CONST();
proxy_MPI_Comm proxy_MPI_COMM_SELF_CONST();
void* proxy_MPI_GROUP_EMPTY_CONST();
void* proxy_MPI_WIN_NULL_CONST();
void* proxy_MPI_FILE_NULL_CONST();
proxy_MPI_Op proxy_MPI_MAX_CONST();
proxy_MPI_Op proxy_MPI_MIN_CONST();
proxy_MPI_Op proxy_MPI_SUM_CONST();
void* proxy_MPI_PROD_CONST();
void* proxy_MPI_LAND_CONST();
void* proxy_MPI_BAND_CONST();
void* proxy_MPI_LOR_CONST();
void* proxy_MPI_BOR_CONST();
void* proxy_MPI_LXOR_CONST();
void* proxy_MPI_BXOR_CONST();
void* proxy_MPI_MINLOC_CONST();
void* proxy_MPI_MAXLOC_CONST();
void* proxy_MPI_REPLACE_CONST();
void* proxy_MPI_TAG_UB_CONST();
void* proxy_MPI_HOST_CONST();
void* proxy_MPI_IO_CONST();
void* proxy_MPI_WTIME_IS_GLOBAL_CONST();
void* proxy_MPI_UNIVERSE_SIZE_CONST();
void* proxy_MPI_LASTUSEDCODE_CONST();
void* proxy_MPI_APPNUM_CONST();
void* proxy_MPI_WIN_BASE_CONST();
void* proxy_MPI_WIN_SIZE_CONST();
void* proxy_MPI_WIN_DISP_UNIT_CONST();
int64_t proxy_MPI_MAX_PROCESSOR_NAME_CONST();
int64_t proxy_MPI_MAX_ERROR_STRING_CONST();
void* proxy_MPI_MAX_PORT_NAME_CONST();
void* proxy_MPI_MAX_OBJECT_NAME_CONST();
int64_t proxy_MPI_UNDEFINED_CONST();
int64_t proxy_MPI_KEYVAL_INVALID_CONST();
void* proxy_MPI_BSEND_OVERHEAD_CONST();
void* proxy_MPI_BOTTOM_CONST();
int64_t proxy_MPI_PROC_NULL_CONST();
int64_t proxy_MPI_ANY_SOURCE_CONST();
void* proxy_MPI_ROOT_CONST();
void* proxy_MPI_ANY_TAG_CONST();
int64_t proxy_MPI_LOCK_EXCLUSIVE_CONST();
int64_t proxy_MPI_LOCK_SHARED_CONST();
void* proxy_MPI_ERRORS_ARE_FATAL_CONST();
void* proxy_MPI_ERRORS_RETURN_CONST();
void* proxy_MPI_NULL_COPY_FN_CONST();
void* proxy_MPI_NULL_DELETE_FN_CONST();
void* proxy_MPI_DUP_FN_CONST();
void* proxy_MPI_COMM_NULL_COPY_FN_CONST();
proxy_MPI_Comm_delete_attr_function* proxy_MPI_COMM_NULL_DELETE_FN_CONST();
proxy_MPI_Comm_copy_attr_function* proxy_MPI_COMM_DUP_FN_CONST();
void* proxy_MPI_WIN_NULL_COPY_FN_CONST();
void* proxy_MPI_WIN_NULL_DELETE_FN_CONST();
void* proxy_MPI_WIN_DUP_FN_CONST();
void* proxy_MPI_TYPE_NULL_COPY_FN_CONST();
void* proxy_MPI_TYPE_NULL_DELETE_FN_CONST();
void* proxy_MPI_TYPE_DUP_FN_CONST();
void* proxy_MPI_INFO_NULL_CONST();
void* proxy_MPI_MAX_INFO_KEY_CONST();
void* proxy_MPI_MAX_INFO_VAL_CONST();
void* proxy_MPI_ORDER_C_CONST();
void* proxy_MPI_ORDER_FORTRAN_CONST();
void* proxy_MPI_DISTRIBUTE_BLOCK_CONST();
void* proxy_MPI_DISTRIBUTE_CYCLIC_CONST();
void* proxy_MPI_DISTRIBUTE_NONE_CONST();
void* proxy_MPI_DISTRIBUTE_DFLT_DARG_CONST();
void* proxy_MPI_IN_PLACE_CONST();
int64_t proxy_MPI_MODE_NOCHECK_CONST();
void* proxy_MPI_MODE_NOSTORE_CONST();
void* proxy_MPI_MODE_NOPUT_CONST();
void* proxy_MPI_MODE_NOPRECEDE_CONST();
void* proxy_MPI_MODE_NOSUCCEED_CONST();
proxy_MPI_Fint proxy_MPI_Comm_c2f(proxy_MPI_Comm comm);
proxy_MPI_Comm proxy_MPI_Comm_f2c(proxy_MPI_Fint comm);
proxy_MPI_Fint proxy_MPI_Type_c2f(proxy_MPI_Datatype type);
proxy_MPI_Datatype proxy_MPI_Type_f2c(proxy_MPI_Fint type);
proxy_MPI_Fint proxy_MPI_Group_c2f(proxy_MPI_Group group);
proxy_MPI_Group proxy_MPI_Group_f2c(proxy_MPI_Fint group);
proxy_MPI_Info proxy_MPI_Info_f2c(proxy_MPI_Fint info);
proxy_MPI_Request proxy_MPI_Request_f2c(proxy_MPI_Fint request);
proxy_MPI_Fint proxy_MPI_Request_c2f(proxy_MPI_Request request);
proxy_MPI_Fint proxy_MPI_Op_c2f(proxy_MPI_Op op);
proxy_MPI_Op proxy_MPI_Op_f2c(proxy_MPI_Fint op);
proxy_MPI_Fint proxy_MPI_Errhandler_c2f(proxy_MPI_Errhandler errhandler);
proxy_MPI_Errhandler proxy_MPI_Errhandler_f2c(proxy_MPI_Fint errhandler);
proxy_MPI_Fint proxy_MPI_Win_c2f(proxy_MPI_Win win);
proxy_MPI_Win proxy_MPI_Win_f2c(proxy_MPI_Fint win);
proxy_MPI_Status* proxy_MPI_STATUS_IGNORE_CONST();
proxy_MPI_Status* proxy_MPI_STATUSES_IGNORE_CONST();
void* proxy_MPI_ERRCODES_IGNORE_CONST();
void* proxy_MPI_ARGV_NULL_CONST();
void* proxy_MPI_ARGVS_NULL_CONST();
void* proxy_MPI_THREAD_SINGLE_CONST();
void* proxy_MPI_THREAD_FUNNELED_CONST();
void* proxy_MPI_THREAD_SERIALIZED_CONST();
void* proxy_MPI_THREAD_MULTIPLE_CONST();
int64_t proxy_MPI_SUCCESS_CONST();
int64_t proxy_MPI_ERR_BUFFER_CONST();
int64_t proxy_MPI_ERR_COUNT_CONST();
int64_t proxy_MPI_ERR_TYPE_CONST();
int64_t proxy_MPI_ERR_TAG_CONST();
int64_t proxy_MPI_ERR_COMM_CONST();
int64_t proxy_MPI_ERR_RANK_CONST();
int64_t proxy_MPI_ERR_ROOT_CONST();
int64_t proxy_MPI_ERR_TRUNCATE_CONST();
int64_t proxy_MPI_ERR_GROUP_CONST();
int64_t proxy_MPI_ERR_OP_CONST();
int64_t proxy_MPI_ERR_REQUEST_CONST();
int64_t proxy_MPI_ERR_TOPOLOGY_CONST();
int64_t proxy_MPI_ERR_DIMS_CONST();
int64_t proxy_MPI_ERR_ARG_CONST();
int64_t proxy_MPI_ERR_OTHER_CONST();
int64_t proxy_MPI_ERR_UNKNOWN_CONST();
int64_t proxy_MPI_ERR_INTERN_CONST();
int64_t proxy_MPI_ERR_IN_STATUS_CONST();
int64_t proxy_MPI_ERR_PENDING_CONST();
int64_t proxy_MPI_ERR_ACCESS_CONST();
int64_t proxy_MPI_ERR_AMODE_CONST();
int64_t proxy_MPI_ERR_BAD_FILE_CONST();
int64_t proxy_MPI_ERR_CONVERSION_CONST();
int64_t proxy_MPI_ERR_DUP_DATAREP_CONST();
int64_t proxy_MPI_ERR_FILE_EXISTS_CONST();
int64_t proxy_MPI_ERR_FILE_IN_USE_CONST();
int64_t proxy_MPI_ERR_FILE_CONST();
int64_t proxy_MPI_ERR_IO_CONST();
int64_t proxy_MPI_ERR_NO_SPACE_CONST();
int64_t proxy_MPI_ERR_NO_SUCH_FILE_CONST();
int64_t proxy_MPI_ERR_READ_ONLY_CONST();
int64_t proxy_MPI_ERR_UNSUPPORTED_DATAREP_CONST();
int64_t proxy_MPI_ERR_INFO_CONST();
int64_t proxy_MPI_ERR_INFO_KEY_CONST();
int64_t proxy_MPI_ERR_INFO_VALUE_CONST();
int64_t proxy_MPI_ERR_INFO_NOKEY_CONST();
int64_t proxy_MPI_ERR_NAME_CONST();
int64_t proxy_MPI_ERR_NO_MEM_CONST();
int64_t proxy_MPI_ERR_NOT_SAME_CONST();
int64_t proxy_MPI_ERR_PORT_CONST();
int64_t proxy_MPI_ERR_QUOTA_CONST();
int64_t proxy_MPI_ERR_SERVICE_CONST();
int64_t proxy_MPI_ERR_SPAWN_CONST();
int64_t proxy_MPI_ERR_UNSUPPORTED_OPERATION_CONST();
int64_t proxy_MPI_ERR_WIN_CONST();
int64_t proxy_MPI_ERR_BASE_CONST();
int64_t proxy_MPI_ERR_LOCKTYPE_CONST();
int64_t proxy_MPI_ERR_KEYVAL_CONST();
int64_t proxy_MPI_ERR_RMA_CONFLICT_CONST();
int64_t proxy_MPI_ERR_RMA_SYNC_CONST();
int64_t proxy_MPI_ERR_SIZE_CONST();
int64_t proxy_MPI_ERR_DISP_CONST();
int64_t proxy_MPI_ERR_ASSERT_CONST();
int64_t proxy_MPI_ERR_LASTCODE_CONST();
void* proxy_MPI_CONVERSION_FN_NULL_CONST();
int64_t proxy_MPI_MODE_RDONLY_CONST();
int64_t proxy_MPI_MODE_RDWR_CONST();
int64_t proxy_MPI_MODE_WRONLY_CONST();
int64_t proxy_MPI_MODE_CREATE_CONST();
int64_t proxy_MPI_MODE_EXCL_CONST();
int64_t proxy_MPI_MODE_DELETE_ON_CLOSE_CONST();
int64_t proxy_MPI_MODE_UNIQUE_OPEN_CONST();
int64_t proxy_MPI_MODE_APPEND_CONST();
int64_t proxy_MPI_MODE_SEQUENTIAL_CONST();
int64_t proxy_MPI_DISPLACEMENT_CURRENT_CONST();
int64_t proxy_MPI_SEEK_SET_CONST();
int64_t proxy_MPI_SEEK_CUR_CONST();
int64_t proxy_MPI_SEEK_END_CONST();
void* proxy_MPI_MAX_DATAREP_STRING_CONST();

#ifdef __cplusplus
}
#endif
