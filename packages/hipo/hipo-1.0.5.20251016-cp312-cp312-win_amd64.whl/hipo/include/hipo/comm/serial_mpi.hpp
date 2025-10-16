
#pragma once

#if defined (_WIN64) || defined (WIN32) || defined (_WIN32)

#ifdef hipo_EXPORTS
#define HIPO_WIN_API __declspec(dllexport)
#else
//#define HIPO_WIN_API __declspec(dllimport)
#define HIPO_WIN_API
#endif

#else

#define HIPO_WIN_API

#endif

#ifdef __cplusplus
extern "C" {
#endif

#define MPI_COMM_NULL ( ( MPI_Comm ) 0x04000000 )
#define MPI_OP_NULL ( ( MPI_Op ) 0x18000000 )
#define MPI_GROUP_NULL ( ( MPI_Group ) 0x08000000 )
#define MPI_DATATYPE_NULL ( ( MPI_Datatype ) 0x0c000000 )
#define MPI_REQUEST_NULL ( ( MPI_Request ) 0x2c000000 )
#define MPI_ERRHANDLER_NULL ( ( MPI_Errhandler ) 0x14000000 )
#define MPI_MESSAGE_NULL ( ( MPI_Message ) 0x2c000000 )
#define MPI_MESSAGE_NO_PROC ( ( MPI_Message ) 0x6c000000 )
#define MPI_IDENT 0
#define MPI_CONGRUENT 1
#define MPI_SIMILAR 2
#define MPI_UNEQUAL 3
#define MPI_CHAR ( ( MPI_Datatype ) 0x4c000101 )
#define MPI_SIGNED_CHAR ( ( MPI_Datatype ) 0x4c000118 )
#define MPI_UNSIGNED_CHAR ( ( MPI_Datatype ) 0x4c000102 )
#define MPI_BYTE ( ( MPI_Datatype ) 0x4c00010d )
#define MPI_WCHAR ( ( MPI_Datatype ) 0x4c00040e )
#define MPI_SHORT ( ( MPI_Datatype ) 0x4c000203 )
#define MPI_UNSIGNED_SHORT ( ( MPI_Datatype ) 0x4c000204 )
#define MPI_INT ( ( MPI_Datatype ) 0x4c000405 )
#define MPI_UNSIGNED ( ( MPI_Datatype ) 0x4c000406 )
#define MPI_LONG ( ( MPI_Datatype ) 0x4c000807 )
#define MPI_UNSIGNED_LONG ( ( MPI_Datatype ) 0x4c000808 )
#define MPI_FLOAT ( ( MPI_Datatype ) 0x4c00040a )
#define MPI_DOUBLE ( ( MPI_Datatype ) 0x4c00080b )
#define MPI_LONG_DOUBLE ( ( MPI_Datatype ) 0x4c00100c )
#define MPI_LONG_LONG_INT ( ( MPI_Datatype ) 0x4c000809 )
#define MPI_UNSIGNED_LONG_LONG ( ( MPI_Datatype ) 0x4c000819 )
#define MPI_LONG_LONG MPI_LONG_LONG_INT
#define MPI_PACKED ( ( MPI_Datatype ) 0x4c00010f )
#define MPI_LB ( ( MPI_Datatype ) 0x4c000010 )
#define MPI_UB ( ( MPI_Datatype ) 0x4c000011 )
#define MPI_FLOAT_INT ( ( MPI_Datatype ) 0x8c000000 )
#define MPI_DOUBLE_INT ( ( MPI_Datatype ) 0x8c000001 )
#define MPI_LONG_INT ( ( MPI_Datatype ) 0x8c000002 )
#define MPI_SHORT_INT ( ( MPI_Datatype ) 0x8c000003 )
#define MPI_2INT ( ( MPI_Datatype ) 0x4c000816 )
#define MPI_LONG_DOUBLE_INT ( ( MPI_Datatype ) 0x8c000004 )
#define MPI_COMPLEX ( ( MPI_Datatype ) 0x4c00081e )
#define MPI_DOUBLE_COMPLEX ( ( MPI_Datatype ) 0x4c001022 )
#define MPI_LOGICAL ( ( MPI_Datatype ) 0x4c00041d )
#define MPI_REAL ( ( MPI_Datatype ) 0x4c00041c )
#define MPI_DOUBLE_PRECISION ( ( MPI_Datatype ) 0x4c00081f )
#define MPI_INTEGER ( ( MPI_Datatype ) 0x4c00041b )
#define MPI_2INTEGER ( ( MPI_Datatype ) 0x4c000820 )
#define MPI_2REAL ( ( MPI_Datatype ) 0x4c000821 )
#define MPI_2DOUBLE_PRECISION ( ( MPI_Datatype ) 0x4c001023 )
#define MPI_CHARACTER ( ( MPI_Datatype ) 0x4c00011a )
#define MPI_REAL4 ( ( MPI_Datatype ) 0x4c000427 )
#define MPI_REAL8 ( ( MPI_Datatype ) 0x4c000829 )
#define MPI_REAL16 ( ( MPI_Datatype ) 0x4c00102b )
#define MPI_COMPLEX8 ( ( MPI_Datatype ) 0x4c000828 )
#define MPI_COMPLEX16 ( ( MPI_Datatype ) 0x4c00102a )
#define MPI_COMPLEX32 ( ( MPI_Datatype ) 0x4c00202c )
#define MPI_INTEGER1 ( ( MPI_Datatype ) 0x4c00012d )
#define MPI_INTEGER2 ( ( MPI_Datatype ) 0x4c00022f )
#define MPI_INTEGER4 ( ( MPI_Datatype ) 0x4c000430 )
#define MPI_INTEGER8 ( ( MPI_Datatype ) 0x4c000831 )
#define MPI_INTEGER16 ( ( MPI_Datatype ) MPI_DATATYPE_NULL )
#define MPI_INT8_T ( ( MPI_Datatype ) 0x4c000137 )
#define MPI_INT16_T ( ( MPI_Datatype ) 0x4c000238 )
#define MPI_INT32_T ( ( MPI_Datatype ) 0x4c000439 )
#define MPI_INT64_T ( ( MPI_Datatype ) 0x4c00083a )
#define MPI_UINT8_T ( ( MPI_Datatype ) 0x4c00013b )
#define MPI_UINT16_T ( ( MPI_Datatype ) 0x4c00023c )
#define MPI_UINT32_T ( ( MPI_Datatype ) 0x4c00043d )
#define MPI_UINT64_T ( ( MPI_Datatype ) 0x4c00083e )
#define MPI_C_BOOL ( ( MPI_Datatype ) 0x4c00013f )
#define MPI_C_FLOAT_COMPLEX ( ( MPI_Datatype ) 0x4c000840 )
#define MPI_C_COMPLEX MPI_C_FLOAT_COMPLEX
#define MPI_C_DOUBLE_COMPLEX ( ( MPI_Datatype ) 0x4c001041 )
#define MPI_C_LONG_DOUBLE_COMPLEX ( ( MPI_Datatype ) 0x4c002042 )
#define MPI_AINT ( ( MPI_Datatype ) 0x4c000843 )
#define MPI_OFFSET ( ( MPI_Datatype ) 0x4c000844 )
#define MPI_COUNT ( ( MPI_Datatype ) 0x4c000845 )
#define MPI_CXX_BOOL ( ( MPI_Datatype ) 0x4c000133 )
#define MPI_CXX_FLOAT_COMPLEX ( ( MPI_Datatype ) 0x4c000834 )
#define MPI_CXX_DOUBLE_COMPLEX ( ( MPI_Datatype ) 0x4c001035 )
#define MPI_CXX_LONG_DOUBLE_COMPLEX ( ( MPI_Datatype ) 0x4c002036 )
#define MPI_TYPECLASS_REAL 1
#define MPI_TYPECLASS_INTEGER 2
#define MPI_TYPECLASS_COMPLEX 3
#define MPI_COMM_WORLD ( ( MPI_Comm ) 0x44000000 )
#define MPI_COMM_SELF ( ( MPI_Comm ) 0x44000001 )
#define MPI_GROUP_EMPTY ( ( MPI_Group ) 0x48000000 )
#define MPI_WIN_NULL ( ( MPI_Win ) 0x20000000 )
#define MPI_SESSION_NULL ( ( MPI_Session ) 0x38000000 )
#define MPI_FILE_DEFINED
#define MPI_FILE_NULL ( ( MPI_File ) 0 )
#define MPI_MAX ( MPI_Op ) ( 0x58000001 )
#define MPI_MIN ( MPI_Op ) ( 0x58000002 )
#define MPI_SUM ( MPI_Op ) ( 0x58000003 )
#define MPI_PROD ( MPI_Op ) ( 0x58000004 )
#define MPI_LAND ( MPI_Op ) ( 0x58000005 )
#define MPI_BAND ( MPI_Op ) ( 0x58000006 )
#define MPI_LOR ( MPI_Op ) ( 0x58000007 )
#define MPI_BOR ( MPI_Op ) ( 0x58000008 )
#define MPI_LXOR ( MPI_Op ) ( 0x58000009 )
#define MPI_BXOR ( MPI_Op ) ( 0x5800000a )
#define MPI_MINLOC ( MPI_Op ) ( 0x5800000b )
#define MPI_MAXLOC ( MPI_Op ) ( 0x5800000c )
#define MPI_REPLACE ( MPI_Op ) ( 0x5800000d )
#define MPI_NO_OP ( MPI_Op ) ( 0x5800000e )
#define MPI_TAG_UB 0x64400001
#define MPI_HOST 0x64400003
#define MPI_IO 0x64400005
#define MPI_WTIME_IS_GLOBAL 0x64400007
#define MPI_UNIVERSE_SIZE 0x64400009
#define MPI_LASTUSEDCODE 0x6440000b
#define MPI_APPNUM 0x6440000d
#define MPI_WIN_BASE 0x66000001
#define MPI_WIN_SIZE 0x66000003
#define MPI_WIN_DISP_UNIT 0x66000005
#define MPI_WIN_CREATE_FLAVOR 0x66000007
#define MPI_WIN_MODEL 0x66000009
#define MPI_MAX_PROCESSOR_NAME 128
#define MPI_MAX_LIBRARY_VERSION_STRING 8192
#define MPI_MAX_ERROR_STRING 512
#define MPI_MAX_PORT_NAME 256
#define MPI_MAX_OBJECT_NAME 128
#define MPI_MAX_STRINGTAG_LEN 256
#define MPI_MAX_PSET_NAME_LEN 256
#define MPI_UNDEFINED ( - 32766 )
#define MPI_KEYVAL_INVALID 0x24000000
#define MPI_BSEND_OVERHEAD 96
#define MPI_BOTTOM ( void * ) 0
#define MPI_PROC_NULL ( - 1 )
#define MPI_ANY_SOURCE ( - 2 )
#define MPI_ROOT ( - 3 )
#define MPI_ANY_TAG ( - 1 )
#define MPI_LOCK_EXCLUSIVE 234
#define MPI_LOCK_SHARED 235
#define MPI_ERRORS_ARE_FATAL ( ( MPI_Errhandler ) 0x54000000 )
#define MPI_ERRORS_RETURN ( ( MPI_Errhandler ) 0x54000001 )
#define MPI_ERRORS_ABORT ( ( MPI_Errhandler ) 0x54000003 )
#define MPI_NULL_COPY_FN ( ( MPI_Copy_function * ) 0 )
#define MPI_NULL_DELETE_FN ( ( MPI_Delete_function * ) 0 )
#define MPI_DUP_FN MPIR_Dup_fn
#define MPI_COMM_NULL_COPY_FN ( ( MPI_Comm_copy_attr_function * ) 0 )
#define MPI_COMM_NULL_DELETE_FN ( ( MPI_Comm_delete_attr_function * ) 0 )
#define MPI_COMM_DUP_FN ( ( MPI_Comm_copy_attr_function * ) MPI_DUP_FN )
#define MPI_WIN_NULL_COPY_FN ( ( MPI_Win_copy_attr_function * ) 0 )
#define MPI_WIN_NULL_DELETE_FN ( ( MPI_Win_delete_attr_function * ) 0 )
#define MPI_WIN_DUP_FN ( ( MPI_Win_copy_attr_function * ) MPI_DUP_FN )
#define MPI_TYPE_NULL_COPY_FN ( ( MPI_Type_copy_attr_function * ) 0 )
#define MPI_TYPE_NULL_DELETE_FN ( ( MPI_Type_delete_attr_function * ) 0 )
#define MPI_TYPE_DUP_FN ( ( MPI_Type_copy_attr_function * ) MPI_DUP_FN )
#define MPI_VERSION 4
#define MPI_SUBVERSION 0
#define MPI_INFO_NULL ( ( MPI_Info ) 0x1c000000 )
#define MPI_INFO_ENV ( ( MPI_Info ) 0x5c000001 )
#define MPI_MAX_INFO_KEY 255
#define MPI_MAX_INFO_VAL 1024
#define MPI_ORDER_C 56
#define MPI_ORDER_FORTRAN 57
#define MPI_DISTRIBUTE_BLOCK 121
#define MPI_DISTRIBUTE_CYCLIC 122
#define MPI_DISTRIBUTE_NONE 123
#define MPI_DISTRIBUTE_DFLT_DARG - 49767
#define MPI_IN_PLACE ( void * ) - 1
#define MPI_MODE_NOCHECK 1024
#define MPI_MODE_NOSTORE 2048
#define MPI_MODE_NOPUT 4096
#define MPI_MODE_NOPRECEDE 8192
#define MPI_MODE_NOSUCCEED 16384
#define MPI_COMM_TYPE_SHARED 1
#define MPI_COMM_TYPE_HW_GUIDED 2
#define MPI_COMM_TYPE_HW_UNGUIDED 3
#define MPI_AINT_FMT_DEC_SPEC "%ld"
#define MPI_AINT_FMT_HEX_SPEC "%lx"
#define MPI_T_ENUM_NULL ( ( MPI_T_enum ) NULL )
#define MPI_T_CVAR_HANDLE_NULL ( ( MPI_T_cvar_handle ) NULL )
#define MPI_T_PVAR_HANDLE_NULL ( ( MPI_T_pvar_handle ) NULL )
#define MPI_T_PVAR_SESSION_NULL ( ( MPI_T_pvar_session ) NULL )
#define MPI_Comm_c2f ( comm ) ( MPI_Fint ) ( comm )
#define MPI_Comm_f2c ( comm ) ( MPI_Comm ) ( comm )
#define MPI_Type_c2f ( datatype ) ( MPI_Fint ) ( datatype )
#define MPI_Type_f2c ( datatype ) ( MPI_Datatype ) ( datatype )
#define MPI_Group_c2f ( group ) ( MPI_Fint ) ( group )
#define MPI_Group_f2c ( group ) ( MPI_Group ) ( group )
#define MPI_Info_c2f ( info ) ( MPI_Fint ) ( info )
#define MPI_Info_f2c ( info ) ( MPI_Info ) ( info )
#define MPI_Request_f2c ( request ) ( MPI_Request ) ( request )
#define MPI_Request_c2f ( request ) ( MPI_Fint ) ( request )
#define MPI_Op_c2f ( op ) ( MPI_Fint ) ( op )
#define MPI_Op_f2c ( op ) ( MPI_Op ) ( op )
#define MPI_Errhandler_c2f ( errhandler ) ( MPI_Fint ) ( errhandler )
#define MPI_Errhandler_f2c ( errhandler ) ( MPI_Errhandler ) ( errhandler )
#define MPI_Win_c2f ( win ) ( MPI_Fint ) ( win )
#define MPI_Win_f2c ( win ) ( MPI_Win ) ( win )
#define MPI_Message_c2f ( msg ) ( ( MPI_Fint ) ( msg ) )
#define MPI_Message_f2c ( msg ) ( ( MPI_Message ) ( msg ) )
#define MPI_Session_c2f ( session ) ( MPI_Fint ) ( session )
#define MPI_Session_f2c ( session ) ( MPI_Session ) ( session )
#define MPI_STATUS_IGNORE ( MPI_Status * ) 1
#define MPI_STATUSES_IGNORE ( MPI_Status * ) 1
#define MPI_ERRCODES_IGNORE ( int * ) 0
#define MPI_ARGV_NULL ( char * * ) 0
#define MPI_ARGVS_NULL ( char * * * ) 0
#define MPI_F_STATUS_SIZE 5
#define MPI_F_SOURCE 2
#define MPI_F_TAG 3
#define MPI_F_ERROR 4
#define MPI_THREAD_SINGLE 0
#define MPI_THREAD_FUNNELED 1
#define MPI_THREAD_SERIALIZED 2
#define MPI_THREAD_MULTIPLE 3
#define MPI_SUCCESS 0
#define MPI_ERR_BUFFER 1
#define MPI_ERR_COUNT 2
#define MPI_ERR_TYPE 3
#define MPI_ERR_TAG 4
#define MPI_ERR_COMM 5
#define MPI_ERR_RANK 6
#define MPI_ERR_ROOT 7
#define MPI_ERR_TRUNCATE 14
#define MPI_ERR_GROUP 8
#define MPI_ERR_OP 9
#define MPI_ERR_REQUEST 19
#define MPI_ERR_TOPOLOGY 10
#define MPI_ERR_DIMS 11
#define MPI_ERR_ARG 12
#define MPI_ERR_OTHER 15
#define MPI_ERR_UNKNOWN 13
#define MPI_ERR_INTERN 16
#define MPI_ERR_IN_STATUS 17
#define MPI_ERR_PENDING 18
#define MPI_ERR_ACCESS 20
#define MPI_ERR_AMODE 21
#define MPI_ERR_BAD_FILE 22
#define MPI_ERR_CONVERSION 23
#define MPI_ERR_DUP_DATAREP 24
#define MPI_ERR_FILE_EXISTS 25
#define MPI_ERR_FILE_IN_USE 26
#define MPI_ERR_FILE 27
#define MPI_ERR_IO 32
#define MPI_ERR_NO_SPACE 36
#define MPI_ERR_NO_SUCH_FILE 37
#define MPI_ERR_READ_ONLY 40
#define MPI_ERR_UNSUPPORTED_DATAREP 43
#define MPI_ERR_INFO 28
#define MPI_ERR_INFO_KEY 29
#define MPI_ERR_INFO_VALUE 30
#define MPI_ERR_INFO_NOKEY 31
#define MPI_ERR_NAME 33
#define MPI_ERR_NO_MEM 34
#define MPI_ERR_NOT_SAME 35
#define MPI_ERR_PORT 38
#define MPI_ERR_QUOTA 39
#define MPI_ERR_SERVICE 41
#define MPI_ERR_SPAWN 42
#define MPI_ERR_UNSUPPORTED_OPERATION 44
#define MPI_ERR_WIN 45
#define MPI_ERR_BASE 46
#define MPI_ERR_LOCKTYPE 47
#define MPI_ERR_KEYVAL 48
#define MPI_ERR_RMA_CONFLICT 49
#define MPI_ERR_RMA_SYNC 50
#define MPI_ERR_SIZE 51
#define MPI_ERR_DISP 52
#define MPI_ERR_ASSERT 53
#define MPI_ERR_RMA_RANGE 55
#define MPI_ERR_RMA_ATTACH 56
#define MPI_ERR_RMA_SHARED 57
#define MPI_ERR_RMA_FLAVOR 58
#define MPI_T_ERR_MEMORY 59
#define MPI_T_ERR_NOT_INITIALIZED 60
#define MPI_T_ERR_CANNOT_INIT 61
#define MPI_T_ERR_INVALID_INDEX 62
#define MPI_T_ERR_INVALID_ITEM 63
#define MPI_T_ERR_INVALID_HANDLE 64
#define MPI_T_ERR_OUT_OF_HANDLES 65
#define MPI_T_ERR_OUT_OF_SESSIONS 66
#define MPI_T_ERR_INVALID_SESSION 67
#define MPI_T_ERR_CVAR_SET_NOT_NOW 68
#define MPI_T_ERR_CVAR_SET_NEVER 69
#define MPI_T_ERR_PVAR_NO_STARTSTOP 70
#define MPI_T_ERR_PVAR_NO_WRITE 71
#define MPI_T_ERR_PVAR_NO_ATOMIC 72
#define MPI_T_ERR_INVALID_NAME 73
#define MPI_T_ERR_INVALID 74
#define MPI_ERR_SESSION 75
#define MPI_ERR_PROC_ABORTED 76
#define MPI_ERR_VALUE_TOO_LARGE 77
#define MPI_T_ERR_NOT_SUPPORTED 78
#define MPI_ERR_LASTCODE 0x3fffffff
#define MPI_CONVERSION_FN_NULL ( ( MPI_Datarep_conversion_function * ) 0 )
#define MPI_CONVERSION_FN_NULL_C ( ( MPI_Datarep_conversion_function_c * ) 0 )
#define MPI_PROTO_H_INCLUDED
#define MPIO_INCLUDE
#define MPIO_Request MPI_Request
#define MPIO_USES_MPI_REQUEST
#define MPIO_Wait MPI_Wait
#define MPIO_Test MPI_Test
#define MPIO_REQUEST_DEFINED
#define MPI_MODE_RDONLY 2
#define MPI_MODE_RDWR 8
#define MPI_MODE_WRONLY 4
#define MPI_MODE_CREATE 1
#define MPI_MODE_EXCL 64
#define MPI_MODE_DELETE_ON_CLOSE 16
#define MPI_MODE_UNIQUE_OPEN 32
#define MPI_MODE_APPEND 128
#define MPI_MODE_SEQUENTIAL 256
#define MPI_DISPLACEMENT_CURRENT - 54278278
#define MPIO_REQUEST_NULL ( ( MPIO_Request ) 0 )
#define MPI_SEEK_SET 600
#define MPI_SEEK_CUR 602
#define MPI_SEEK_END 604
#define MPI_MAX_DATAREP_STRING 128
typedef int MPI_Datatype;
typedef int MPI_Comm;
typedef int MPI_Group;
typedef int MPI_Win;
typedef int MPI_Session;
typedef struct ADIOI_FileD * MPI_File;
typedef int MPI_Op;
typedef void ( MPI_Handler_function ) ( MPI_Comm * , int * , ... );
typedef int ( MPI_Comm_copy_attr_function ) ( MPI_Comm , int , void * , void * , void * , int * );
typedef int ( MPI_Comm_delete_attr_function ) ( MPI_Comm , int , void * , void * );
typedef int ( MPI_Type_copy_attr_function ) ( MPI_Datatype , int , void * , void * , void * , int * );
typedef int ( MPI_Type_delete_attr_function ) ( MPI_Datatype , int , void * , void * );
typedef int ( MPI_Win_copy_attr_function ) ( MPI_Win , int , void * , void * , void * , int * );
typedef int ( MPI_Win_delete_attr_function ) ( MPI_Win , int , void * , void * );
typedef void ( MPI_Comm_errhandler_function ) ( MPI_Comm * , int * , ... );
typedef void ( MPI_File_errhandler_function ) ( MPI_File * , int * , ... );
typedef void ( MPI_Win_errhandler_function ) ( MPI_Win * , int * , ... );
typedef void ( MPI_Session_errhandler_function ) ( MPI_Session * , int * , ... );
typedef MPI_Comm_errhandler_function MPI_Comm_errhandler_fn;
typedef MPI_File_errhandler_function MPI_File_errhandler_fn;
typedef MPI_Win_errhandler_function MPI_Win_errhandler_fn;
typedef MPI_Session_errhandler_function MPI_Session_errhandler_fn;
typedef int MPI_Errhandler;
typedef int MPI_Request;
typedef int MPI_Message;
typedef int ( MPI_Copy_function ) ( MPI_Comm , int , void * , void * , void * , int * );
typedef int ( MPI_Delete_function ) ( MPI_Comm , int , void * , void * );
typedef int MPI_Info;
typedef long MPI_Aint;
typedef int MPI_Fint;
typedef long MPI_Count;
typedef long MPI_Offset;
typedef struct MPI_Status { int count_lo ; int count_hi_and_cancelled ; int MPI_SOURCE ; int MPI_TAG ; int MPI_ERROR ; } MPI_Status;
typedef void ( MPI_User_function ) ( void * , void * , int * , MPI_Datatype * );
typedef void ( MPI_User_function_c ) ( void * , void * , MPI_Count * , MPI_Datatype * );
typedef struct MPIR_T_enum_s * MPI_T_enum;
typedef struct MPIR_T_cvar_handle_s * MPI_T_cvar_handle;
typedef struct MPIR_T_pvar_handle_s * MPI_T_pvar_handle;
typedef struct MPIR_T_pvar_session_s * MPI_T_pvar_session;
typedef struct MPIR_T_event_registration_s * MPI_T_event_registration;
typedef struct MPIR_T_event_instance_s * MPI_T_event_instance;
typedef enum MPI_T_cb_safety { MPI_T_CB_REQUIRE_NONE = 0 , MPI_T_CB_REQUIRE_MPI_RESTRICTED , MPI_T_CB_REQUIRE_THREAD_SAFE , MPI_T_CB_REQUIRE_ASYNC_SIGNAL_SAFE } MPI_T_cb_safety;
typedef enum MPI_T_source_order { MPI_T_SOURCE_ORDERED = 0 , MPI_T_SOURCE_UNORDERED } MPI_T_source_order;
typedef void ( MPI_T_event_cb_function ) ( MPI_T_event_instance event_instance , MPI_T_event_registration event_registration , MPI_T_cb_safety cb_safety , void * user_data );
typedef void ( MPI_T_event_free_cb_function ) ( MPI_T_event_registration event_registration , MPI_T_cb_safety cb_safety , void * user_data );
typedef void ( MPI_T_event_dropped_cb_function ) ( MPI_Count count , MPI_T_event_registration event_registration , int source_index , MPI_T_cb_safety cb_safety , void * user_data );
typedef struct { MPI_Fint count_lo ; MPI_Fint count_hi_and_cancelled ; MPI_Fint MPI_SOURCE ; MPI_Fint MPI_TAG ; MPI_Fint MPI_ERROR ; } MPI_F08_status;
typedef int ( MPI_Grequest_cancel_function ) ( void * , int );
typedef int ( MPI_Grequest_free_function ) ( void * );
typedef int ( MPI_Grequest_query_function ) ( void * , MPI_Status * );
typedef int ( MPI_Datarep_conversion_function ) ( void * , MPI_Datatype , int , void * , MPI_Offset , void * );
typedef int ( MPI_Datarep_extent_function ) ( MPI_Datatype datatype , MPI_Aint * , void * );
typedef int ( MPI_Datarep_conversion_function_c ) ( void * , MPI_Datatype , MPI_Count , void * , MPI_Offset , void * );
int HIPO_WIN_API MPI_Status_c2f ( const MPI_Status * c_status , MPI_Fint * f_status );
int HIPO_WIN_API MPI_Status_f2c ( const MPI_Fint * f_status , MPI_Status * c_status );
int HIPO_WIN_API MPI_Status_f082c ( const MPI_F08_status * f08_status , MPI_Status * c_status );
int HIPO_WIN_API MPI_Status_c2f08 ( const MPI_Status * c_status , MPI_F08_status * f08_status );
int HIPO_WIN_API MPI_Status_f082f ( const MPI_F08_status * f08_status , MPI_Fint * f_status );
int HIPO_WIN_API MPI_Status_f2f08 ( const MPI_Fint * f_status , MPI_F08_status * f08_status );
int HIPO_WIN_API MPI_Type_create_f90_integer ( int r , MPI_Datatype * newtype );
int HIPO_WIN_API MPI_Type_create_f90_real ( int p , int r , MPI_Datatype * newtype );
int HIPO_WIN_API MPI_Type_create_f90_complex ( int p , int r , MPI_Datatype * newtype );
int HIPO_WIN_API MPI_Attr_delete ( MPI_Comm comm , int keyval );
int HIPO_WIN_API MPI_Attr_get ( MPI_Comm comm , int keyval , void * attribute_val , int * flag );
int HIPO_WIN_API MPI_Attr_put ( MPI_Comm comm , int keyval , void * attribute_val );
int HIPO_WIN_API MPI_Comm_create_keyval ( MPI_Comm_copy_attr_function * comm_copy_attr_fn , MPI_Comm_delete_attr_function * comm_delete_attr_fn , int * comm_keyval , void * extra_state );
int HIPO_WIN_API MPI_Comm_delete_attr ( MPI_Comm comm , int comm_keyval );
int HIPO_WIN_API MPI_Comm_free_keyval ( int * comm_keyval );
int HIPO_WIN_API MPI_Comm_get_attr ( MPI_Comm comm , int comm_keyval , void * attribute_val , int * flag );
int HIPO_WIN_API MPI_Comm_set_attr ( MPI_Comm comm , int comm_keyval , void * attribute_val );
int HIPO_WIN_API MPI_Keyval_create ( MPI_Copy_function * copy_fn , MPI_Delete_function * delete_fn , int * keyval , void * extra_state );
int HIPO_WIN_API MPI_Keyval_free ( int * keyval );
int HIPO_WIN_API MPI_Type_create_keyval ( MPI_Type_copy_attr_function * type_copy_attr_fn , MPI_Type_delete_attr_function * type_delete_attr_fn , int * type_keyval , void * extra_state );
int HIPO_WIN_API MPI_Type_delete_attr ( MPI_Datatype datatype , int type_keyval );
int HIPO_WIN_API MPI_Type_free_keyval ( int * type_keyval );
int HIPO_WIN_API MPI_Type_get_attr ( MPI_Datatype datatype , int type_keyval , void * attribute_val , int * flag );
int HIPO_WIN_API MPI_Type_set_attr ( MPI_Datatype datatype , int type_keyval , void * attribute_val );
int HIPO_WIN_API MPI_Win_create_keyval ( MPI_Win_copy_attr_function * win_copy_attr_fn , MPI_Win_delete_attr_function * win_delete_attr_fn , int * win_keyval , void * extra_state );
int HIPO_WIN_API MPI_Win_delete_attr ( MPI_Win win , int win_keyval );
int HIPO_WIN_API MPI_Win_free_keyval ( int * win_keyval );
int HIPO_WIN_API MPI_Win_get_attr ( MPI_Win win , int win_keyval , void * attribute_val , int * flag );
int HIPO_WIN_API MPI_Win_set_attr ( MPI_Win win , int win_keyval , void * attribute_val );
int HIPO_WIN_API MPI_Allgather ( const void * sendbuf , int sendcount , MPI_Datatype sendtype , void * recvbuf , int recvcount , MPI_Datatype recvtype , MPI_Comm comm );
int HIPO_WIN_API MPI_Allgather_init ( const void * sendbuf , int sendcount , MPI_Datatype sendtype , void * recvbuf , int recvcount , MPI_Datatype recvtype , MPI_Comm comm , MPI_Info info , MPI_Request * request );
int HIPO_WIN_API MPI_Allgatherv ( const void * sendbuf , int sendcount , MPI_Datatype sendtype , void * recvbuf , const int recvcounts [ ] , const int displs [ ] , MPI_Datatype recvtype , MPI_Comm comm );
int HIPO_WIN_API MPI_Allgatherv_init ( const void * sendbuf , int sendcount , MPI_Datatype sendtype , void * recvbuf , const int recvcounts [ ] , const int displs [ ] , MPI_Datatype recvtype , MPI_Comm comm , MPI_Info info , MPI_Request * request );
int HIPO_WIN_API MPI_Allreduce ( const void * sendbuf , void * recvbuf , int count , MPI_Datatype datatype , MPI_Op op , MPI_Comm comm );
int HIPO_WIN_API MPI_Allreduce_init ( const void * sendbuf , void * recvbuf , int count , MPI_Datatype datatype , MPI_Op op , MPI_Comm comm , MPI_Info info , MPI_Request * request );
int HIPO_WIN_API MPI_Alltoall ( const void * sendbuf , int sendcount , MPI_Datatype sendtype , void * recvbuf , int recvcount , MPI_Datatype recvtype , MPI_Comm comm );
int HIPO_WIN_API MPI_Alltoall_init ( const void * sendbuf , int sendcount , MPI_Datatype sendtype , void * recvbuf , int recvcount , MPI_Datatype recvtype , MPI_Comm comm , MPI_Info info , MPI_Request * request );
int HIPO_WIN_API MPI_Alltoallv ( const void * sendbuf , const int sendcounts [ ] , const int sdispls [ ] , MPI_Datatype sendtype , void * recvbuf , const int recvcounts [ ] , const int rdispls [ ] , MPI_Datatype recvtype , MPI_Comm comm );
int HIPO_WIN_API MPI_Alltoallv_init ( const void * sendbuf , const int sendcounts [ ] , const int sdispls [ ] , MPI_Datatype sendtype , void * recvbuf , const int recvcounts [ ] , const int rdispls [ ] , MPI_Datatype recvtype , MPI_Comm comm , MPI_Info info , MPI_Request * request );
int HIPO_WIN_API MPI_Alltoallw ( const void * sendbuf , const int sendcounts [ ] , const int sdispls [ ] , const MPI_Datatype sendtypes [ ] , void * recvbuf , const int recvcounts [ ] , const int rdispls [ ] , const MPI_Datatype recvtypes [ ] , MPI_Comm comm );
int HIPO_WIN_API MPI_Alltoallw_init ( const void * sendbuf , const int sendcounts [ ] , const int sdispls [ ] , const MPI_Datatype sendtypes [ ] , void * recvbuf , const int recvcounts [ ] , const int rdispls [ ] , const MPI_Datatype recvtypes [ ] , MPI_Comm comm , MPI_Info info , MPI_Request * request );
int HIPO_WIN_API MPI_Barrier ( MPI_Comm comm );
int HIPO_WIN_API MPI_Barrier_init ( MPI_Comm comm , MPI_Info info , MPI_Request * request );
int HIPO_WIN_API MPI_Bcast ( void * buffer , int count , MPI_Datatype datatype , int root , MPI_Comm comm );
int HIPO_WIN_API MPI_Bcast_init ( void * buffer , int count , MPI_Datatype datatype , int root , MPI_Comm comm , MPI_Info info , MPI_Request * request );
int HIPO_WIN_API MPI_Exscan ( const void * sendbuf , void * recvbuf , int count , MPI_Datatype datatype , MPI_Op op , MPI_Comm comm );
int HIPO_WIN_API MPI_Exscan_init ( const void * sendbuf , void * recvbuf , int count , MPI_Datatype datatype , MPI_Op op , MPI_Comm comm , MPI_Info info , MPI_Request * request );
int HIPO_WIN_API MPI_Gather ( const void * sendbuf , int sendcount , MPI_Datatype sendtype , void * recvbuf , int recvcount , MPI_Datatype recvtype , int root , MPI_Comm comm );
int HIPO_WIN_API MPI_Gather_init ( const void * sendbuf , int sendcount , MPI_Datatype sendtype , void * recvbuf , int recvcount , MPI_Datatype recvtype , int root , MPI_Comm comm , MPI_Info info , MPI_Request * request );
int HIPO_WIN_API MPI_Gatherv ( const void * sendbuf , int sendcount , MPI_Datatype sendtype , void * recvbuf , const int recvcounts [ ] , const int displs [ ] , MPI_Datatype recvtype , int root , MPI_Comm comm );
int HIPO_WIN_API MPI_Gatherv_init ( const void * sendbuf , int sendcount , MPI_Datatype sendtype , void * recvbuf , const int recvcounts [ ] , const int displs [ ] , MPI_Datatype recvtype , int root , MPI_Comm comm , MPI_Info info , MPI_Request * request );
int HIPO_WIN_API MPI_Iallgather ( const void * sendbuf , int sendcount , MPI_Datatype sendtype , void * recvbuf , int recvcount , MPI_Datatype recvtype , MPI_Comm comm , MPI_Request * request );
int HIPO_WIN_API MPI_Iallgatherv ( const void * sendbuf , int sendcount , MPI_Datatype sendtype , void * recvbuf , const int recvcounts [ ] , const int displs [ ] , MPI_Datatype recvtype , MPI_Comm comm , MPI_Request * request );
int HIPO_WIN_API MPI_Iallreduce ( const void * sendbuf , void * recvbuf , int count , MPI_Datatype datatype , MPI_Op op , MPI_Comm comm , MPI_Request * request );
int HIPO_WIN_API MPI_Ialltoall ( const void * sendbuf , int sendcount , MPI_Datatype sendtype , void * recvbuf , int recvcount , MPI_Datatype recvtype , MPI_Comm comm , MPI_Request * request );
int HIPO_WIN_API MPI_Ialltoallv ( const void * sendbuf , const int sendcounts [ ] , const int sdispls [ ] , MPI_Datatype sendtype , void * recvbuf , const int recvcounts [ ] , const int rdispls [ ] , MPI_Datatype recvtype , MPI_Comm comm , MPI_Request * request );
int HIPO_WIN_API MPI_Ialltoallw ( const void * sendbuf , const int sendcounts [ ] , const int sdispls [ ] , const MPI_Datatype sendtypes [ ] , void * recvbuf , const int recvcounts [ ] , const int rdispls [ ] , const MPI_Datatype recvtypes [ ] , MPI_Comm comm , MPI_Request * request );
int HIPO_WIN_API MPI_Ibarrier ( MPI_Comm comm , MPI_Request * request );
int HIPO_WIN_API MPI_Ibcast ( void * buffer , int count , MPI_Datatype datatype , int root , MPI_Comm comm , MPI_Request * request );
int HIPO_WIN_API MPI_Iexscan ( const void * sendbuf , void * recvbuf , int count , MPI_Datatype datatype , MPI_Op op , MPI_Comm comm , MPI_Request * request );
int HIPO_WIN_API MPI_Igather ( const void * sendbuf , int sendcount , MPI_Datatype sendtype , void * recvbuf , int recvcount , MPI_Datatype recvtype , int root , MPI_Comm comm , MPI_Request * request );
int HIPO_WIN_API MPI_Igatherv ( const void * sendbuf , int sendcount , MPI_Datatype sendtype , void * recvbuf , const int recvcounts [ ] , const int displs [ ] , MPI_Datatype recvtype , int root , MPI_Comm comm , MPI_Request * request );
int HIPO_WIN_API MPI_Ineighbor_allgather ( const void * sendbuf , int sendcount , MPI_Datatype sendtype , void * recvbuf , int recvcount , MPI_Datatype recvtype , MPI_Comm comm , MPI_Request * request );
int HIPO_WIN_API MPI_Ineighbor_allgatherv ( const void * sendbuf , int sendcount , MPI_Datatype sendtype , void * recvbuf , const int recvcounts [ ] , const int displs [ ] , MPI_Datatype recvtype , MPI_Comm comm , MPI_Request * request );
int HIPO_WIN_API MPI_Ineighbor_alltoall ( const void * sendbuf , int sendcount , MPI_Datatype sendtype , void * recvbuf , int recvcount , MPI_Datatype recvtype , MPI_Comm comm , MPI_Request * request );
int HIPO_WIN_API MPI_Ineighbor_alltoallv ( const void * sendbuf , const int sendcounts [ ] , const int sdispls [ ] , MPI_Datatype sendtype , void * recvbuf , const int recvcounts [ ] , const int rdispls [ ] , MPI_Datatype recvtype , MPI_Comm comm , MPI_Request * request );
int HIPO_WIN_API MPI_Ineighbor_alltoallw ( const void * sendbuf , const int sendcounts [ ] , const MPI_Aint sdispls [ ] , const MPI_Datatype sendtypes [ ] , void * recvbuf , const int recvcounts [ ] , const MPI_Aint rdispls [ ] , const MPI_Datatype recvtypes [ ] , MPI_Comm comm , MPI_Request * request );
int HIPO_WIN_API MPI_Ireduce ( const void * sendbuf , void * recvbuf , int count , MPI_Datatype datatype , MPI_Op op , int root , MPI_Comm comm , MPI_Request * request );
int HIPO_WIN_API MPI_Ireduce_scatter ( const void * sendbuf , void * recvbuf , const int recvcounts [ ] , MPI_Datatype datatype , MPI_Op op , MPI_Comm comm , MPI_Request * request );
int HIPO_WIN_API MPI_Ireduce_scatter_block ( const void * sendbuf , void * recvbuf , int recvcount , MPI_Datatype datatype , MPI_Op op , MPI_Comm comm , MPI_Request * request );
int HIPO_WIN_API MPI_Iscan ( const void * sendbuf , void * recvbuf , int count , MPI_Datatype datatype , MPI_Op op , MPI_Comm comm , MPI_Request * request );
int HIPO_WIN_API MPI_Iscatter ( const void * sendbuf , int sendcount , MPI_Datatype sendtype , void * recvbuf , int recvcount , MPI_Datatype recvtype , int root , MPI_Comm comm , MPI_Request * request );
int HIPO_WIN_API MPI_Iscatterv ( const void * sendbuf , const int sendcounts [ ] , const int displs [ ] , MPI_Datatype sendtype , void * recvbuf , int recvcount , MPI_Datatype recvtype , int root , MPI_Comm comm , MPI_Request * request );
int HIPO_WIN_API MPI_Neighbor_allgather ( const void * sendbuf , int sendcount , MPI_Datatype sendtype , void * recvbuf , int recvcount , MPI_Datatype recvtype , MPI_Comm comm );
int HIPO_WIN_API MPI_Neighbor_allgather_init ( const void * sendbuf , int sendcount , MPI_Datatype sendtype , void * recvbuf , int recvcount , MPI_Datatype recvtype , MPI_Comm comm , MPI_Info info , MPI_Request * request );
int HIPO_WIN_API MPI_Neighbor_allgatherv ( const void * sendbuf , int sendcount , MPI_Datatype sendtype , void * recvbuf , const int recvcounts [ ] , const int displs [ ] , MPI_Datatype recvtype , MPI_Comm comm );
int HIPO_WIN_API MPI_Neighbor_allgatherv_init ( const void * sendbuf , int sendcount , MPI_Datatype sendtype , void * recvbuf , const int recvcounts [ ] , const int displs [ ] , MPI_Datatype recvtype , MPI_Comm comm , MPI_Info info , MPI_Request * request );
int HIPO_WIN_API MPI_Neighbor_alltoall ( const void * sendbuf , int sendcount , MPI_Datatype sendtype , void * recvbuf , int recvcount , MPI_Datatype recvtype , MPI_Comm comm );
int HIPO_WIN_API MPI_Neighbor_alltoall_init ( const void * sendbuf , int sendcount , MPI_Datatype sendtype , void * recvbuf , int recvcount , MPI_Datatype recvtype , MPI_Comm comm , MPI_Info info , MPI_Request * request );
int HIPO_WIN_API MPI_Neighbor_alltoallv ( const void * sendbuf , const int sendcounts [ ] , const int sdispls [ ] , MPI_Datatype sendtype , void * recvbuf , const int recvcounts [ ] , const int rdispls [ ] , MPI_Datatype recvtype , MPI_Comm comm );
int HIPO_WIN_API MPI_Neighbor_alltoallv_init ( const void * sendbuf , const int sendcounts [ ] , const int sdispls [ ] , MPI_Datatype sendtype , void * recvbuf , const int recvcounts [ ] , const int rdispls [ ] , MPI_Datatype recvtype , MPI_Comm comm , MPI_Info info , MPI_Request * request );
int HIPO_WIN_API MPI_Neighbor_alltoallw ( const void * sendbuf , const int sendcounts [ ] , const MPI_Aint sdispls [ ] , const MPI_Datatype sendtypes [ ] , void * recvbuf , const int recvcounts [ ] , const MPI_Aint rdispls [ ] , const MPI_Datatype recvtypes [ ] , MPI_Comm comm );
int HIPO_WIN_API MPI_Neighbor_alltoallw_init ( const void * sendbuf , const int sendcounts [ ] , const MPI_Aint sdispls [ ] , const MPI_Datatype sendtypes [ ] , void * recvbuf , const int recvcounts [ ] , const MPI_Aint rdispls [ ] , const MPI_Datatype recvtypes [ ] , MPI_Comm comm , MPI_Info info , MPI_Request * request );
int HIPO_WIN_API MPI_Reduce ( const void * sendbuf , void * recvbuf , int count , MPI_Datatype datatype , MPI_Op op , int root , MPI_Comm comm );
int HIPO_WIN_API MPI_Reduce_init ( const void * sendbuf , void * recvbuf , int count , MPI_Datatype datatype , MPI_Op op , int root , MPI_Comm comm , MPI_Info info , MPI_Request * request );
int HIPO_WIN_API MPI_Reduce_local ( const void * inbuf , void * inoutbuf , int count , MPI_Datatype datatype , MPI_Op op );
int HIPO_WIN_API MPI_Reduce_scatter ( const void * sendbuf , void * recvbuf , const int recvcounts [ ] , MPI_Datatype datatype , MPI_Op op , MPI_Comm comm );
int HIPO_WIN_API MPI_Reduce_scatter_block ( const void * sendbuf , void * recvbuf , int recvcount , MPI_Datatype datatype , MPI_Op op , MPI_Comm comm );
int HIPO_WIN_API MPI_Reduce_scatter_block_init ( const void * sendbuf , void * recvbuf , int recvcount , MPI_Datatype datatype , MPI_Op op , MPI_Comm comm , MPI_Info info , MPI_Request * request );
int HIPO_WIN_API MPI_Reduce_scatter_init ( const void * sendbuf , void * recvbuf , const int recvcounts [ ] , MPI_Datatype datatype , MPI_Op op , MPI_Comm comm , MPI_Info info , MPI_Request * request );
int HIPO_WIN_API MPI_Scan ( const void * sendbuf , void * recvbuf , int count , MPI_Datatype datatype , MPI_Op op , MPI_Comm comm );
int HIPO_WIN_API MPI_Scan_init ( const void * sendbuf , void * recvbuf , int count , MPI_Datatype datatype , MPI_Op op , MPI_Comm comm , MPI_Info info , MPI_Request * request );
int HIPO_WIN_API MPI_Scatter ( const void * sendbuf , int sendcount , MPI_Datatype sendtype , void * recvbuf , int recvcount , MPI_Datatype recvtype , int root , MPI_Comm comm );
int HIPO_WIN_API MPI_Scatter_init ( const void * sendbuf , int sendcount , MPI_Datatype sendtype , void * recvbuf , int recvcount , MPI_Datatype recvtype , int root , MPI_Comm comm , MPI_Info info , MPI_Request * request );
int HIPO_WIN_API MPI_Scatterv ( const void * sendbuf , const int sendcounts [ ] , const int displs [ ] , MPI_Datatype sendtype , void * recvbuf , int recvcount , MPI_Datatype recvtype , int root , MPI_Comm comm );
int HIPO_WIN_API MPI_Scatterv_init ( const void * sendbuf , const int sendcounts [ ] , const int displs [ ] , MPI_Datatype sendtype , void * recvbuf , int recvcount , MPI_Datatype recvtype , int root , MPI_Comm comm , MPI_Info info , MPI_Request * request );
int HIPO_WIN_API MPI_Comm_compare ( MPI_Comm comm1 , MPI_Comm comm2 , int * result );
int HIPO_WIN_API MPI_Comm_create ( MPI_Comm comm , MPI_Group group , MPI_Comm * newcomm );
int HIPO_WIN_API MPI_Comm_create_group ( MPI_Comm comm , MPI_Group group , int tag , MPI_Comm * newcomm );
int HIPO_WIN_API MPI_Comm_dup ( MPI_Comm comm , MPI_Comm * newcomm );
int HIPO_WIN_API MPI_Comm_dup_with_info ( MPI_Comm comm , MPI_Info info , MPI_Comm * newcomm );
int HIPO_WIN_API MPI_Comm_free ( MPI_Comm * comm );
int HIPO_WIN_API MPI_Comm_get_info ( MPI_Comm comm , MPI_Info * info_used );
int HIPO_WIN_API MPI_Comm_get_name ( MPI_Comm comm , char * comm_name , int * resultlen );
int HIPO_WIN_API MPI_Comm_group ( MPI_Comm comm , MPI_Group * group );
int HIPO_WIN_API MPI_Comm_idup ( MPI_Comm comm , MPI_Comm * newcomm , MPI_Request * request );
int HIPO_WIN_API MPI_Comm_idup_with_info ( MPI_Comm comm , MPI_Info info , MPI_Comm * newcomm , MPI_Request * request );
int HIPO_WIN_API MPI_Comm_rank ( MPI_Comm comm , int * rank );
int HIPO_WIN_API MPI_Comm_remote_group ( MPI_Comm comm , MPI_Group * group );
int HIPO_WIN_API MPI_Comm_remote_size ( MPI_Comm comm , int * size );
int HIPO_WIN_API MPI_Comm_set_info ( MPI_Comm comm , MPI_Info info );
int HIPO_WIN_API MPI_Comm_set_name ( MPI_Comm comm , const char * comm_name );
int HIPO_WIN_API MPI_Comm_size ( MPI_Comm comm , int * size );
int HIPO_WIN_API MPI_Comm_split ( MPI_Comm comm , int color , int key , MPI_Comm * newcomm );
int HIPO_WIN_API MPI_Comm_split_type ( MPI_Comm comm , int split_type , int key , MPI_Info info , MPI_Comm * newcomm );
int HIPO_WIN_API MPI_Comm_test_inter ( MPI_Comm comm , int * flag );
int HIPO_WIN_API MPI_Intercomm_create ( MPI_Comm local_comm , int local_leader , MPI_Comm peer_comm , int remote_leader , int tag , MPI_Comm * newintercomm );
int HIPO_WIN_API MPI_Intercomm_create_from_groups ( MPI_Group local_group , int local_leader , MPI_Group remote_group , int remote_leader , const char * stringtag , MPI_Info info , MPI_Errhandler errhandler , MPI_Comm * newintercomm );
int HIPO_WIN_API MPI_Intercomm_merge ( MPI_Comm intercomm , int high , MPI_Comm * newintracomm );
int HIPO_WIN_API MPI_Get_address ( const void * location , MPI_Aint * address );
int HIPO_WIN_API MPI_Get_count ( const MPI_Status * status , MPI_Datatype datatype , int * count );
int HIPO_WIN_API MPI_Get_elements ( const MPI_Status * status , MPI_Datatype datatype , int * count );
int HIPO_WIN_API MPI_Get_elements_x ( const MPI_Status * status , MPI_Datatype datatype , MPI_Count * count );
int HIPO_WIN_API MPI_Pack ( const void * inbuf , int incount , MPI_Datatype datatype , void * outbuf , int outsize , int * position , MPI_Comm comm );
int HIPO_WIN_API MPI_Pack_external ( const char * datarep , const void * inbuf , int incount , MPI_Datatype datatype , void * outbuf , MPI_Aint outsize , MPI_Aint * position );
int HIPO_WIN_API MPI_Pack_external_size ( const char * datarep , int incount , MPI_Datatype datatype , MPI_Aint * size );
int HIPO_WIN_API MPI_Pack_size ( int incount , MPI_Datatype datatype , MPI_Comm comm , int * size );
int HIPO_WIN_API MPI_Status_set_elements ( MPI_Status * status , MPI_Datatype datatype , int count );
int HIPO_WIN_API MPI_Status_set_elements_x ( MPI_Status * status , MPI_Datatype datatype , MPI_Count count );
int HIPO_WIN_API MPI_Type_commit ( MPI_Datatype * datatype );
int HIPO_WIN_API MPI_Type_contiguous ( int count , MPI_Datatype oldtype , MPI_Datatype * newtype );
int HIPO_WIN_API MPI_Type_create_darray ( int size , int rank , int ndims , const int array_of_gsizes [ ] , const int array_of_distribs [ ] , const int array_of_dargs [ ] , const int array_of_psizes [ ] , int order , MPI_Datatype oldtype , MPI_Datatype * newtype );
int HIPO_WIN_API MPI_Type_create_hindexed ( int count , const int array_of_blocklengths [ ] , const MPI_Aint array_of_displacements [ ] , MPI_Datatype oldtype , MPI_Datatype * newtype );
int HIPO_WIN_API MPI_Type_create_hindexed_block ( int count , int blocklength , const MPI_Aint array_of_displacements [ ] , MPI_Datatype oldtype , MPI_Datatype * newtype );
int HIPO_WIN_API MPI_Type_create_hvector ( int count , int blocklength , MPI_Aint stride , MPI_Datatype oldtype , MPI_Datatype * newtype );
int HIPO_WIN_API MPI_Type_create_indexed_block ( int count , int blocklength , const int array_of_displacements [ ] , MPI_Datatype oldtype , MPI_Datatype * newtype );
int HIPO_WIN_API MPI_Type_create_resized ( MPI_Datatype oldtype , MPI_Aint lb , MPI_Aint extent , MPI_Datatype * newtype );
int HIPO_WIN_API MPI_Type_create_struct ( int count , const int array_of_blocklengths [ ] , const MPI_Aint array_of_displacements [ ] , const MPI_Datatype array_of_types [ ] , MPI_Datatype * newtype );
int HIPO_WIN_API MPI_Type_create_subarray ( int ndims , const int array_of_sizes [ ] , const int array_of_subsizes [ ] , const int array_of_starts [ ] , int order , MPI_Datatype oldtype , MPI_Datatype * newtype );
int HIPO_WIN_API MPI_Type_dup ( MPI_Datatype oldtype , MPI_Datatype * newtype );
int HIPO_WIN_API MPI_Type_free ( MPI_Datatype * datatype );
int HIPO_WIN_API MPI_Type_get_contents ( MPI_Datatype datatype , int max_integers , int max_addresses , int max_datatypes , int array_of_integers [ ] , MPI_Aint array_of_addresses [ ] , MPI_Datatype array_of_datatypes [ ] );
int HIPO_WIN_API MPI_Type_get_envelope ( MPI_Datatype datatype , int * num_integers , int * num_addresses , int * num_datatypes , int * combiner );
int HIPO_WIN_API MPI_Type_get_extent ( MPI_Datatype datatype , MPI_Aint * lb , MPI_Aint * extent );
int HIPO_WIN_API MPI_Type_get_extent_x ( MPI_Datatype datatype , MPI_Count * lb , MPI_Count * extent );
int HIPO_WIN_API MPI_Type_get_name ( MPI_Datatype datatype , char * type_name , int * resultlen );
int HIPO_WIN_API MPI_Type_get_true_extent ( MPI_Datatype datatype , MPI_Aint * true_lb , MPI_Aint * true_extent );
int HIPO_WIN_API MPI_Type_get_true_extent_x ( MPI_Datatype datatype , MPI_Count * true_lb , MPI_Count * true_extent );
int HIPO_WIN_API MPI_Type_indexed ( int count , const int array_of_blocklengths [ ] , const int array_of_displacements [ ] , MPI_Datatype oldtype , MPI_Datatype * newtype );
int HIPO_WIN_API MPI_Type_match_size ( int typeclass , int size , MPI_Datatype * datatype );
int HIPO_WIN_API MPI_Type_set_name ( MPI_Datatype datatype , const char * type_name );
int HIPO_WIN_API MPI_Type_size ( MPI_Datatype datatype , int * size );
int HIPO_WIN_API MPI_Type_size_x ( MPI_Datatype datatype , MPI_Count * size );
int HIPO_WIN_API MPI_Type_vector ( int count , int blocklength , int stride , MPI_Datatype oldtype , MPI_Datatype * newtype );
int HIPO_WIN_API MPI_Unpack ( const void * inbuf , int insize , int * position , void * outbuf , int outcount , MPI_Datatype datatype , MPI_Comm comm );
int HIPO_WIN_API MPI_Unpack_external ( const char datarep [ ] , const void * inbuf , MPI_Aint insize , MPI_Aint * position , void * outbuf , int outcount , MPI_Datatype datatype );
int HIPO_WIN_API MPI_Address ( void * location , MPI_Aint * address );
int HIPO_WIN_API MPI_Type_extent ( MPI_Datatype datatype , MPI_Aint * extent );
int HIPO_WIN_API MPI_Type_lb ( MPI_Datatype datatype , MPI_Aint * displacement );
int HIPO_WIN_API MPI_Type_ub ( MPI_Datatype datatype , MPI_Aint * displacement );
int HIPO_WIN_API MPI_Type_hindexed ( int count , int array_of_blocklengths [ ] , MPI_Aint array_of_displacements [ ] , MPI_Datatype oldtype , MPI_Datatype * newtype );
int HIPO_WIN_API MPI_Type_hvector ( int count , int blocklength , MPI_Aint stride , MPI_Datatype oldtype , MPI_Datatype * newtype );
int HIPO_WIN_API MPI_Type_struct ( int count , int array_of_blocklengths [ ] , MPI_Aint array_of_displacements [ ] , MPI_Datatype array_of_types [ ] , MPI_Datatype * newtype );
int HIPO_WIN_API MPI_Add_error_class ( int * errorclass );
int HIPO_WIN_API MPI_Add_error_code ( int errorclass , int * errorcode );
int HIPO_WIN_API MPI_Add_error_string ( int errorcode , const char * string );
int HIPO_WIN_API MPI_Comm_call_errhandler ( MPI_Comm comm , int errorcode );
int HIPO_WIN_API MPI_Comm_create_errhandler ( MPI_Comm_errhandler_function * comm_errhandler_fn , MPI_Errhandler * errhandler );
int HIPO_WIN_API MPI_Comm_get_errhandler ( MPI_Comm comm , MPI_Errhandler * errhandler );
int HIPO_WIN_API MPI_Comm_set_errhandler ( MPI_Comm comm , MPI_Errhandler errhandler );
int HIPO_WIN_API MPI_Errhandler_free ( MPI_Errhandler * errhandler );
int HIPO_WIN_API MPI_Error_class ( int errorcode , int * errorclass );
int HIPO_WIN_API MPI_Error_string ( int errorcode , char * string , int * resultlen );
int HIPO_WIN_API MPI_File_call_errhandler ( MPI_File fh , int errorcode );
int HIPO_WIN_API MPI_File_create_errhandler ( MPI_File_errhandler_function * file_errhandler_fn , MPI_Errhandler * errhandler );
int HIPO_WIN_API MPI_File_get_errhandler ( MPI_File file , MPI_Errhandler * errhandler );
int HIPO_WIN_API MPI_File_set_errhandler ( MPI_File file , MPI_Errhandler errhandler );
int HIPO_WIN_API MPI_Session_call_errhandler ( MPI_Session session , int errorcode );
int HIPO_WIN_API MPI_Session_create_errhandler ( MPI_Session_errhandler_function * session_errhandler_fn , MPI_Errhandler * errhandler );
int HIPO_WIN_API MPI_Session_get_errhandler ( MPI_Session session , MPI_Errhandler * errhandler );
int HIPO_WIN_API MPI_Session_set_errhandler ( MPI_Session session , MPI_Errhandler errhandler );
int HIPO_WIN_API MPI_Win_call_errhandler ( MPI_Win win , int errorcode );
int HIPO_WIN_API MPI_Win_create_errhandler ( MPI_Win_errhandler_function * win_errhandler_fn , MPI_Errhandler * errhandler );
int HIPO_WIN_API MPI_Win_get_errhandler ( MPI_Win win , MPI_Errhandler * errhandler );
int HIPO_WIN_API MPI_Win_set_errhandler ( MPI_Win win , MPI_Errhandler errhandler );
int HIPO_WIN_API MPI_Errhandler_create ( MPI_Comm_errhandler_function * comm_errhandler_fn , MPI_Errhandler * errhandler );
int HIPO_WIN_API MPI_Errhandler_get ( MPI_Comm comm , MPI_Errhandler * errhandler );
int HIPO_WIN_API MPI_Errhandler_set ( MPI_Comm comm , MPI_Errhandler errhandler );
int HIPO_WIN_API MPI_Group_compare ( MPI_Group group1 , MPI_Group group2 , int * result );
int HIPO_WIN_API MPI_Group_difference ( MPI_Group group1 , MPI_Group group2 , MPI_Group * newgroup );
int HIPO_WIN_API MPI_Group_excl ( MPI_Group group , int n , const int ranks [ ] , MPI_Group * newgroup );
int HIPO_WIN_API MPI_Group_free ( MPI_Group * group );
int HIPO_WIN_API MPI_Group_incl ( MPI_Group group , int n , const int ranks [ ] , MPI_Group * newgroup );
int HIPO_WIN_API MPI_Group_intersection ( MPI_Group group1 , MPI_Group group2 , MPI_Group * newgroup );
int HIPO_WIN_API MPI_Group_range_excl ( MPI_Group group , int n , int ranges [ ] [ 3 ] , MPI_Group * newgroup );
int HIPO_WIN_API MPI_Group_range_incl ( MPI_Group group , int n , int ranges [ ] [ 3 ] , MPI_Group * newgroup );
int HIPO_WIN_API MPI_Group_rank ( MPI_Group group , int * rank );
int HIPO_WIN_API MPI_Group_size ( MPI_Group group , int * size );
int HIPO_WIN_API MPI_Group_translate_ranks ( MPI_Group group1 , int n , const int ranks1 [ ] , MPI_Group group2 , int ranks2 [ ] );
int HIPO_WIN_API MPI_Group_union ( MPI_Group group1 , MPI_Group group2 , MPI_Group * newgroup );
int HIPO_WIN_API MPI_Info_create ( MPI_Info * info );
int HIPO_WIN_API MPI_Info_create_env ( int argc , char * argv [ ] , MPI_Info * info );
int HIPO_WIN_API MPI_Info_delete ( MPI_Info info , const char * key );
int HIPO_WIN_API MPI_Info_dup ( MPI_Info info , MPI_Info * newinfo );
int HIPO_WIN_API MPI_Info_free ( MPI_Info * info );
int HIPO_WIN_API MPI_Info_get ( MPI_Info info , const char * key , int valuelen , char * value , int * flag );
int HIPO_WIN_API MPI_Info_get_nkeys ( MPI_Info info , int * nkeys );
int HIPO_WIN_API MPI_Info_get_nthkey ( MPI_Info info , int n , char * key );
int HIPO_WIN_API MPI_Info_get_string ( MPI_Info info , const char * key , int * buflen , char * value , int * flag );
int HIPO_WIN_API MPI_Info_get_valuelen ( MPI_Info info , const char * key , int * valuelen , int * flag );
int HIPO_WIN_API MPI_Info_set ( MPI_Info info , const char * key , const char * value );
int HIPO_WIN_API MPI_Abort ( MPI_Comm comm , int errorcode );
int HIPO_WIN_API MPI_Comm_create_from_group ( MPI_Group group , const char * stringtag , MPI_Info info , MPI_Errhandler errhandler , MPI_Comm * newcomm );
int HIPO_WIN_API MPI_Finalize ( void );
int HIPO_WIN_API MPI_Finalized ( int * flag );
int HIPO_WIN_API MPI_Group_from_session_pset ( MPI_Session session , const char * pset_name , MPI_Group * newgroup );
int HIPO_WIN_API MPI_Init ( int * argc , char * * * argv );
int HIPO_WIN_API MPI_Init_thread ( int * argc , char * * * argv , int required , int * provided );
int HIPO_WIN_API MPI_Initialized ( int * flag );
int HIPO_WIN_API MPI_Is_thread_main ( int * flag );
int HIPO_WIN_API MPI_Query_thread ( int * provided );
int HIPO_WIN_API MPI_Session_finalize ( MPI_Session * session );
int HIPO_WIN_API MPI_Session_get_info ( MPI_Session session , MPI_Info * info_used );
int HIPO_WIN_API MPI_Session_get_nth_pset ( MPI_Session session , MPI_Info info , int n , int * pset_len , char * pset_name );
int HIPO_WIN_API MPI_Session_get_num_psets ( MPI_Session session , MPI_Info info , int * npset_names );
int HIPO_WIN_API MPI_Session_get_pset_info ( MPI_Session session , const char * pset_name , MPI_Info * info );
int HIPO_WIN_API MPI_Session_init ( MPI_Info info , MPI_Errhandler errhandler , MPI_Session * session );
MPI_Aint HIPO_WIN_API MPI_Aint_add ( MPI_Aint base , MPI_Aint disp );
MPI_Aint HIPO_WIN_API MPI_Aint_diff ( MPI_Aint addr1 , MPI_Aint addr2 );
int HIPO_WIN_API MPI_Get_library_version ( char * version , int * resultlen );
int HIPO_WIN_API MPI_Get_processor_name ( char * name , int * resultlen );
int HIPO_WIN_API MPI_Get_version ( int * version , int * subversion );
int HIPO_WIN_API MPI_Pcontrol ( const int level , ... );
int HIPO_WIN_API MPI_Op_commutative ( MPI_Op op , int * commute );
int HIPO_WIN_API MPI_Op_create ( MPI_User_function * user_fn , int commute , MPI_Op * op );
int HIPO_WIN_API MPI_Op_free ( MPI_Op * op );
int HIPO_WIN_API MPI_Parrived ( MPI_Request request , int partition , int * flag );
int HIPO_WIN_API MPI_Pready ( int partition , MPI_Request request );
int HIPO_WIN_API MPI_Pready_list ( int length , int array_of_partitions [ ] , MPI_Request request );
int HIPO_WIN_API MPI_Pready_range ( int partition_low , int partition_high , MPI_Request request );
int HIPO_WIN_API MPI_Precv_init ( void * buf , int partitions , MPI_Count count , MPI_Datatype datatype , int dest , int tag , MPI_Comm comm , MPI_Info info , MPI_Request * request );
int HIPO_WIN_API MPI_Psend_init ( void * buf , int partitions , MPI_Count count , MPI_Datatype datatype , int dest , int tag , MPI_Comm comm , MPI_Info info , MPI_Request * request );
int HIPO_WIN_API MPI_Bsend ( const void * buf , int count , MPI_Datatype datatype , int dest , int tag , MPI_Comm comm );
int HIPO_WIN_API MPI_Bsend_init ( const void * buf , int count , MPI_Datatype datatype , int dest , int tag , MPI_Comm comm , MPI_Request * request );
int HIPO_WIN_API MPI_Buffer_attach ( void * buffer , int size );
int HIPO_WIN_API MPI_Buffer_detach ( void * buffer_addr , int * size );
int HIPO_WIN_API MPI_Ibsend ( const void * buf , int count , MPI_Datatype datatype , int dest , int tag , MPI_Comm comm , MPI_Request * request );
int HIPO_WIN_API MPI_Improbe ( int source , int tag , MPI_Comm comm , int * flag , MPI_Message * message , MPI_Status * status );
int HIPO_WIN_API MPI_Imrecv ( void * buf , int count , MPI_Datatype datatype , MPI_Message * message , MPI_Request * request );
int HIPO_WIN_API MPI_Iprobe ( int source , int tag , MPI_Comm comm , int * flag , MPI_Status * status );
int HIPO_WIN_API MPI_Irecv ( void * buf , int count , MPI_Datatype datatype , int source , int tag , MPI_Comm comm , MPI_Request * request );
int HIPO_WIN_API MPI_Irsend ( const void * buf , int count , MPI_Datatype datatype , int dest , int tag , MPI_Comm comm , MPI_Request * request );
int HIPO_WIN_API MPI_Isend ( const void * buf , int count , MPI_Datatype datatype , int dest , int tag , MPI_Comm comm , MPI_Request * request );
int HIPO_WIN_API MPI_Isendrecv ( const void * sendbuf , int sendcount , MPI_Datatype sendtype , int dest , int sendtag , void * recvbuf , int recvcount , MPI_Datatype recvtype , int source , int recvtag , MPI_Comm comm , MPI_Request * request );
int HIPO_WIN_API MPI_Isendrecv_replace ( void * buf , int count , MPI_Datatype datatype , int dest , int sendtag , int source , int recvtag , MPI_Comm comm , MPI_Request * request );
int HIPO_WIN_API MPI_Issend ( const void * buf , int count , MPI_Datatype datatype , int dest , int tag , MPI_Comm comm , MPI_Request * request );
int HIPO_WIN_API MPI_Mprobe ( int source , int tag , MPI_Comm comm , MPI_Message * message , MPI_Status * status );
int HIPO_WIN_API MPI_Mrecv ( void * buf , int count , MPI_Datatype datatype , MPI_Message * message , MPI_Status * status );
int HIPO_WIN_API MPI_Probe ( int source , int tag , MPI_Comm comm , MPI_Status * status );
int HIPO_WIN_API MPI_Recv ( void * buf , int count , MPI_Datatype datatype , int source , int tag , MPI_Comm comm , MPI_Status * status );
int HIPO_WIN_API MPI_Recv_init ( void * buf , int count , MPI_Datatype datatype , int source , int tag , MPI_Comm comm , MPI_Request * request );
int HIPO_WIN_API MPI_Rsend ( const void * buf , int count , MPI_Datatype datatype , int dest , int tag , MPI_Comm comm );
int HIPO_WIN_API MPI_Rsend_init ( const void * buf , int count , MPI_Datatype datatype , int dest , int tag , MPI_Comm comm , MPI_Request * request );
int HIPO_WIN_API MPI_Send ( const void * buf , int count , MPI_Datatype datatype , int dest , int tag , MPI_Comm comm );
int HIPO_WIN_API MPI_Send_init ( const void * buf , int count , MPI_Datatype datatype , int dest , int tag , MPI_Comm comm , MPI_Request * request );
int HIPO_WIN_API MPI_Sendrecv ( const void * sendbuf , int sendcount , MPI_Datatype sendtype , int dest , int sendtag , void * recvbuf , int recvcount , MPI_Datatype recvtype , int source , int recvtag , MPI_Comm comm , MPI_Status * status );
int HIPO_WIN_API MPI_Sendrecv_replace ( void * buf , int count , MPI_Datatype datatype , int dest , int sendtag , int source , int recvtag , MPI_Comm comm , MPI_Status * status );
int HIPO_WIN_API MPI_Ssend ( const void * buf , int count , MPI_Datatype datatype , int dest , int tag , MPI_Comm comm );
int HIPO_WIN_API MPI_Ssend_init ( const void * buf , int count , MPI_Datatype datatype , int dest , int tag , MPI_Comm comm , MPI_Request * request );
int HIPO_WIN_API MPI_Cancel ( MPI_Request * request );
int HIPO_WIN_API MPI_Grequest_complete ( MPI_Request request );
int HIPO_WIN_API MPI_Grequest_start ( MPI_Grequest_query_function * query_fn , MPI_Grequest_free_function * free_fn , MPI_Grequest_cancel_function * cancel_fn , void * extra_state , MPI_Request * request );
int HIPO_WIN_API MPI_Request_free ( MPI_Request * request );
int HIPO_WIN_API MPI_Request_get_status ( MPI_Request request , int * flag , MPI_Status * status );
int HIPO_WIN_API MPI_Start ( MPI_Request * request );
int HIPO_WIN_API MPI_Startall ( int count , MPI_Request array_of_requests [ ] );
int HIPO_WIN_API MPI_Status_set_cancelled ( MPI_Status * status , int flag );
int HIPO_WIN_API MPI_Test ( MPI_Request * request , int * flag , MPI_Status * status );
int HIPO_WIN_API MPI_Test_cancelled ( const MPI_Status * status , int * flag );
int HIPO_WIN_API MPI_Testall ( int count , MPI_Request array_of_requests [ ] , int * flag , MPI_Status array_of_statuses [ ] );
int HIPO_WIN_API MPI_Testany ( int count , MPI_Request array_of_requests [ ] , int * indx , int * flag , MPI_Status * status );
int HIPO_WIN_API MPI_Testsome ( int incount , MPI_Request array_of_requests [ ] , int * outcount , int array_of_indices [ ] , MPI_Status array_of_statuses [ ] );
int HIPO_WIN_API MPI_Wait ( MPI_Request * request , MPI_Status * status );
int HIPO_WIN_API MPI_Waitall ( int count , MPI_Request array_of_requests [ ] , MPI_Status array_of_statuses [ ] );
int HIPO_WIN_API MPI_Waitany ( int count , MPI_Request array_of_requests [ ] , int * indx , MPI_Status * status );
int HIPO_WIN_API MPI_Waitsome ( int incount , MPI_Request array_of_requests [ ] , int * outcount , int array_of_indices [ ] , MPI_Status array_of_statuses [ ] );
int HIPO_WIN_API MPI_Accumulate ( const void * origin_addr , int origin_count , MPI_Datatype origin_datatype , int target_rank , MPI_Aint target_disp , int target_count , MPI_Datatype target_datatype , MPI_Op op , MPI_Win win );
int HIPO_WIN_API MPI_Alloc_mem ( MPI_Aint size , MPI_Info info , void * baseptr );
int HIPO_WIN_API MPI_Compare_and_swap ( const void * origin_addr , const void * compare_addr , void * result_addr , MPI_Datatype datatype , int target_rank , MPI_Aint target_disp , MPI_Win win );
int HIPO_WIN_API MPI_Fetch_and_op ( const void * origin_addr , void * result_addr , MPI_Datatype datatype , int target_rank , MPI_Aint target_disp , MPI_Op op , MPI_Win win );
int HIPO_WIN_API MPI_Free_mem ( void * base );
int HIPO_WIN_API MPI_Get ( void * origin_addr , int origin_count , MPI_Datatype origin_datatype , int target_rank , MPI_Aint target_disp , int target_count , MPI_Datatype target_datatype , MPI_Win win );
int HIPO_WIN_API MPI_Get_accumulate ( const void * origin_addr , int origin_count , MPI_Datatype origin_datatype , void * result_addr , int result_count , MPI_Datatype result_datatype , int target_rank , MPI_Aint target_disp , int target_count , MPI_Datatype target_datatype , MPI_Op op , MPI_Win win );
int HIPO_WIN_API MPI_Put ( const void * origin_addr , int origin_count , MPI_Datatype origin_datatype , int target_rank , MPI_Aint target_disp , int target_count , MPI_Datatype target_datatype , MPI_Win win );
int HIPO_WIN_API MPI_Raccumulate ( const void * origin_addr , int origin_count , MPI_Datatype origin_datatype , int target_rank , MPI_Aint target_disp , int target_count , MPI_Datatype target_datatype , MPI_Op op , MPI_Win win , MPI_Request * request );
int HIPO_WIN_API MPI_Rget ( void * origin_addr , int origin_count , MPI_Datatype origin_datatype , int target_rank , MPI_Aint target_disp , int target_count , MPI_Datatype target_datatype , MPI_Win win , MPI_Request * request );
int HIPO_WIN_API MPI_Rget_accumulate ( const void * origin_addr , int origin_count , MPI_Datatype origin_datatype , void * result_addr , int result_count , MPI_Datatype result_datatype , int target_rank , MPI_Aint target_disp , int target_count , MPI_Datatype target_datatype , MPI_Op op , MPI_Win win , MPI_Request * request );
int HIPO_WIN_API MPI_Rput ( const void * origin_addr , int origin_count , MPI_Datatype origin_datatype , int target_rank , MPI_Aint target_disp , int target_count , MPI_Datatype target_datatype , MPI_Win win , MPI_Request * request );
int HIPO_WIN_API MPI_Win_allocate ( MPI_Aint size , int disp_unit , MPI_Info info , MPI_Comm comm , void * baseptr , MPI_Win * win );
int HIPO_WIN_API MPI_Win_allocate_shared ( MPI_Aint size , int disp_unit , MPI_Info info , MPI_Comm comm , void * baseptr , MPI_Win * win );
int HIPO_WIN_API MPI_Win_attach ( MPI_Win win , void * base , MPI_Aint size );
int HIPO_WIN_API MPI_Win_complete ( MPI_Win win );
int HIPO_WIN_API MPI_Win_create ( void * base , MPI_Aint size , int disp_unit , MPI_Info info , MPI_Comm comm , MPI_Win * win );
int HIPO_WIN_API MPI_Win_create_dynamic ( MPI_Info info , MPI_Comm comm , MPI_Win * win );
int HIPO_WIN_API MPI_Win_detach ( MPI_Win win , const void * base );
int HIPO_WIN_API MPI_Win_fence ( int assert , MPI_Win win );
int HIPO_WIN_API MPI_Win_flush ( int rank , MPI_Win win );
int HIPO_WIN_API MPI_Win_flush_all ( MPI_Win win );
int HIPO_WIN_API MPI_Win_flush_local ( int rank , MPI_Win win );
int HIPO_WIN_API MPI_Win_flush_local_all ( MPI_Win win );
int HIPO_WIN_API MPI_Win_free ( MPI_Win * win );
int HIPO_WIN_API MPI_Win_get_group ( MPI_Win win , MPI_Group * group );
int HIPO_WIN_API MPI_Win_get_info ( MPI_Win win , MPI_Info * info_used );
int HIPO_WIN_API MPI_Win_get_name ( MPI_Win win , char * win_name , int * resultlen );
int HIPO_WIN_API MPI_Win_lock ( int lock_type , int rank , int assert , MPI_Win win );
int HIPO_WIN_API MPI_Win_lock_all ( int assert , MPI_Win win );
int HIPO_WIN_API MPI_Win_post ( MPI_Group group , int assert , MPI_Win win );
int HIPO_WIN_API MPI_Win_set_info ( MPI_Win win , MPI_Info info );
int HIPO_WIN_API MPI_Win_set_name ( MPI_Win win , const char * win_name );
int HIPO_WIN_API MPI_Win_shared_query ( MPI_Win win , int rank , MPI_Aint * size , int * disp_unit , void * baseptr );
int HIPO_WIN_API MPI_Win_start ( MPI_Group group , int assert , MPI_Win win );
int HIPO_WIN_API MPI_Win_sync ( MPI_Win win );
int HIPO_WIN_API MPI_Win_test ( MPI_Win win , int * flag );
int HIPO_WIN_API MPI_Win_unlock ( int rank , MPI_Win win );
int HIPO_WIN_API MPI_Win_unlock_all ( MPI_Win win );
int HIPO_WIN_API MPI_Win_wait ( MPI_Win win );
int HIPO_WIN_API MPI_Close_port ( const char * port_name );
int HIPO_WIN_API MPI_Comm_accept ( const char * port_name , MPI_Info info , int root , MPI_Comm comm , MPI_Comm * newcomm );
int HIPO_WIN_API MPI_Comm_connect ( const char * port_name , MPI_Info info , int root , MPI_Comm comm , MPI_Comm * newcomm );
int HIPO_WIN_API MPI_Comm_disconnect ( MPI_Comm * comm );
int HIPO_WIN_API MPI_Comm_get_parent ( MPI_Comm * parent );
int HIPO_WIN_API MPI_Comm_join ( int fd , MPI_Comm * intercomm );
int HIPO_WIN_API MPI_Comm_spawn ( const char * command , char * argv [ ] , int maxprocs , MPI_Info info , int root , MPI_Comm comm , MPI_Comm * intercomm , int array_of_errcodes [ ] );
int HIPO_WIN_API MPI_Comm_spawn_multiple ( int count , char * array_of_commands [ ] , char * * array_of_argv [ ] , const int array_of_maxprocs [ ] , const MPI_Info array_of_info [ ] , int root , MPI_Comm comm , MPI_Comm * intercomm , int array_of_errcodes [ ] );
int HIPO_WIN_API MPI_Lookup_name ( const char * service_name , MPI_Info info , char * port_name );
int HIPO_WIN_API MPI_Open_port ( MPI_Info info , char * port_name );
int HIPO_WIN_API MPI_Publish_name ( const char * service_name , MPI_Info info , const char * port_name );
int HIPO_WIN_API MPI_Unpublish_name ( const char * service_name , MPI_Info info , const char * port_name );
double HIPO_WIN_API MPI_Wtick ( void );
double HIPO_WIN_API MPI_Wtime ( void );
int HIPO_WIN_API MPI_Cart_coords ( MPI_Comm comm , int rank , int maxdims , int coords [ ] );
int HIPO_WIN_API MPI_Cart_create ( MPI_Comm comm_old , int ndims , const int dims [ ] , const int periods [ ] , int reorder , MPI_Comm * comm_cart );
int HIPO_WIN_API MPI_Cart_get ( MPI_Comm comm , int maxdims , int dims [ ] , int periods [ ] , int coords [ ] );
int HIPO_WIN_API MPI_Cart_map ( MPI_Comm comm , int ndims , const int dims [ ] , const int periods [ ] , int * newrank );
int HIPO_WIN_API MPI_Cart_rank ( MPI_Comm comm , const int coords [ ] , int * rank );
int HIPO_WIN_API MPI_Cart_shift ( MPI_Comm comm , int direction , int disp , int * rank_source , int * rank_dest );
int HIPO_WIN_API MPI_Cart_sub ( MPI_Comm comm , const int remain_dims [ ] , MPI_Comm * newcomm );
int HIPO_WIN_API MPI_Cartdim_get ( MPI_Comm comm , int * ndims );
int HIPO_WIN_API MPI_Dims_create ( int nnodes , int ndims , int dims [ ] );
int HIPO_WIN_API MPI_Dist_graph_create ( MPI_Comm comm_old , int n , const int sources [ ] , const int degrees [ ] , const int destinations [ ] , const int weights [ ] , MPI_Info info , int reorder , MPI_Comm * comm_dist_graph );
int HIPO_WIN_API MPI_Dist_graph_create_adjacent ( MPI_Comm comm_old , int indegree , const int sources [ ] , const int sourceweights [ ] , int outdegree , const int destinations [ ] , const int destweights [ ] , MPI_Info info , int reorder , MPI_Comm * comm_dist_graph );
int HIPO_WIN_API MPI_Dist_graph_neighbors ( MPI_Comm comm , int maxindegree , int sources [ ] , int sourceweights [ ] , int maxoutdegree , int destinations [ ] , int destweights [ ] );
int HIPO_WIN_API MPI_Dist_graph_neighbors_count ( MPI_Comm comm , int * indegree , int * outdegree , int * weighted );
int HIPO_WIN_API MPI_Graph_create ( MPI_Comm comm_old , int nnodes , const int indx [ ] , const int edges [ ] , int reorder , MPI_Comm * comm_graph );
int HIPO_WIN_API MPI_Graph_get ( MPI_Comm comm , int maxindex , int maxedges , int indx [ ] , int edges [ ] );
int HIPO_WIN_API MPI_Graph_map ( MPI_Comm comm , int nnodes , const int indx [ ] , const int edges [ ] , int * newrank );
int HIPO_WIN_API MPI_Graph_neighbors ( MPI_Comm comm , int rank , int maxneighbors , int neighbors [ ] );
int HIPO_WIN_API MPI_Graph_neighbors_count ( MPI_Comm comm , int rank , int * nneighbors );
int HIPO_WIN_API MPI_Graphdims_get ( MPI_Comm comm , int * nnodes , int * nedges );
int HIPO_WIN_API MPI_Topo_test ( MPI_Comm comm , int * status );
int HIPO_WIN_API MPI_T_category_changed ( int * update_number );
int HIPO_WIN_API MPI_T_category_get_categories ( int cat_index , int len , int indices [ ] );
int HIPO_WIN_API MPI_T_category_get_cvars ( int cat_index , int len , int indices [ ] );
int HIPO_WIN_API MPI_T_category_get_events ( int cat_index , int len , int indices [ ] );
int HIPO_WIN_API MPI_T_category_get_index ( const char * name , int * cat_index );
int HIPO_WIN_API MPI_T_category_get_info ( int cat_index , char * name , int * name_len , char * desc , int * desc_len , int * num_cvars , int * num_pvars , int * num_categories );
int HIPO_WIN_API MPI_T_category_get_num ( int * num_cat );
int HIPO_WIN_API MPI_T_category_get_num_events ( int cat_index , int * num_events );
int HIPO_WIN_API MPI_T_category_get_pvars ( int cat_index , int len , int indices [ ] );
int HIPO_WIN_API MPI_T_cvar_get_index ( const char * name , int * cvar_index );
int HIPO_WIN_API MPI_T_cvar_get_info ( int cvar_index , char * name , int * name_len , int * verbosity , MPI_Datatype * datatype , MPI_T_enum * enumtype , char * desc , int * desc_len , int * bind , int * scope );
int HIPO_WIN_API MPI_T_cvar_get_num ( int * num_cvar );
int HIPO_WIN_API MPI_T_cvar_handle_alloc ( int cvar_index , void * obj_handle , MPI_T_cvar_handle * handle , int * count );
int HIPO_WIN_API MPI_T_cvar_handle_free ( MPI_T_cvar_handle * handle );
int HIPO_WIN_API MPI_T_cvar_read ( MPI_T_cvar_handle handle , void * buf );
int HIPO_WIN_API MPI_T_cvar_write ( MPI_T_cvar_handle handle , const void * buf );
int HIPO_WIN_API MPI_T_enum_get_info ( MPI_T_enum enumtype , int * num , char * name , int * name_len );
int HIPO_WIN_API MPI_T_enum_get_item ( MPI_T_enum enumtype , int indx , int * value , char * name , int * name_len );
int HIPO_WIN_API MPI_T_event_callback_get_info ( MPI_T_event_registration event_registration , MPI_T_cb_safety cb_safety , MPI_Info * info_used );
int HIPO_WIN_API MPI_T_event_callback_set_info ( MPI_T_event_registration event_registration , MPI_T_cb_safety cb_safety , MPI_Info info );
int HIPO_WIN_API MPI_T_event_copy ( MPI_T_event_instance event_instance , void * buffer );
int HIPO_WIN_API MPI_T_event_get_index ( const char * name , int * event_index );
int HIPO_WIN_API MPI_T_event_get_info ( int event_index , char * name , int * name_len , int * verbosity , MPI_Datatype array_of_datatypes [ ] , MPI_Aint array_of_displacements [ ] , int * num_elements , MPI_T_enum * enumtype , MPI_Info * info , char * desc , int * desc_len , int * bind );
int HIPO_WIN_API MPI_T_event_get_num ( int * num_events );
int HIPO_WIN_API MPI_T_event_get_source ( MPI_T_event_instance event_instance , int * source_index );
int HIPO_WIN_API MPI_T_event_get_timestamp ( MPI_T_event_instance event_instance , MPI_Count * event_timestamp );
int HIPO_WIN_API MPI_T_event_handle_alloc ( int event_index , void * obj_handle , MPI_Info info , MPI_T_event_registration * event_registration );
int HIPO_WIN_API MPI_T_event_handle_free ( MPI_T_event_registration event_registration , void * user_data , MPI_T_event_free_cb_function free_cb_function );
int HIPO_WIN_API MPI_T_event_handle_get_info ( MPI_T_event_registration event_registration , MPI_Info * info_used );
int HIPO_WIN_API MPI_T_event_handle_set_info ( MPI_T_event_registration event_registration , MPI_Info info );
int HIPO_WIN_API MPI_T_event_read ( MPI_T_event_instance event_instance , int element_index , void * buffer );
int HIPO_WIN_API MPI_T_event_register_callback ( MPI_T_event_registration event_registration , MPI_T_cb_safety cb_safety , MPI_Info info , void * user_data , MPI_T_event_cb_function event_cb_function );
int HIPO_WIN_API MPI_T_event_set_dropped_handler ( MPI_T_event_registration event_registration , MPI_T_event_dropped_cb_function dropped_cb_function );
int HIPO_WIN_API MPI_T_finalize ( void );
int HIPO_WIN_API MPI_T_init_thread ( int required , int * provided );
int HIPO_WIN_API MPI_T_pvar_get_index ( const char * name , int var_class , int * pvar_index );
int HIPO_WIN_API MPI_T_pvar_get_info ( int pvar_index , char * name , int * name_len , int * verbosity , int * var_class , MPI_Datatype * datatype , MPI_T_enum * enumtype , char * desc , int * desc_len , int * bind , int * readonly , int * continuous , int * atomic );
int HIPO_WIN_API MPI_T_pvar_get_num ( int * num_pvar );
int HIPO_WIN_API MPI_T_pvar_handle_alloc ( MPI_T_pvar_session session , int pvar_index , void * obj_handle , MPI_T_pvar_handle * handle , int * count );
int HIPO_WIN_API MPI_T_pvar_handle_free ( MPI_T_pvar_session session , MPI_T_pvar_handle * handle );
int HIPO_WIN_API MPI_T_pvar_read ( MPI_T_pvar_session session , MPI_T_pvar_handle handle , void * buf );
int HIPO_WIN_API MPI_T_pvar_readreset ( MPI_T_pvar_session session , MPI_T_pvar_handle handle , void * buf );
int HIPO_WIN_API MPI_T_pvar_reset ( MPI_T_pvar_session session , MPI_T_pvar_handle handle );
int HIPO_WIN_API MPI_T_pvar_session_create ( MPI_T_pvar_session * session );
int HIPO_WIN_API MPI_T_pvar_session_free ( MPI_T_pvar_session * session );
int HIPO_WIN_API MPI_T_pvar_start ( MPI_T_pvar_session session , MPI_T_pvar_handle handle );
int HIPO_WIN_API MPI_T_pvar_stop ( MPI_T_pvar_session session , MPI_T_pvar_handle handle );
int HIPO_WIN_API MPI_T_pvar_write ( MPI_T_pvar_session session , MPI_T_pvar_handle handle , const void * buf );
int HIPO_WIN_API MPI_T_source_get_info ( int source_index , char * name , int * name_len , char * desc , int * desc_len , MPI_T_source_order * ordering , MPI_Count * ticks_per_second , MPI_Count * max_ticks , MPI_Info * info );
int HIPO_WIN_API MPI_T_source_get_num ( int * num_sources );
int HIPO_WIN_API MPI_T_source_get_timestamp ( int source_index , MPI_Count * timestamp );
int HIPO_WIN_API MPI_Allgather_c ( const void * sendbuf , MPI_Count sendcount , MPI_Datatype sendtype , void * recvbuf , MPI_Count recvcount , MPI_Datatype recvtype , MPI_Comm comm );
int HIPO_WIN_API MPI_Allgather_init_c ( const void * sendbuf , MPI_Count sendcount , MPI_Datatype sendtype , void * recvbuf , MPI_Count recvcount , MPI_Datatype recvtype , MPI_Comm comm , MPI_Info info , MPI_Request * request );
int HIPO_WIN_API MPI_Allgatherv_c ( const void * sendbuf , MPI_Count sendcount , MPI_Datatype sendtype , void * recvbuf , const MPI_Count recvcounts [ ] , const MPI_Aint displs [ ] , MPI_Datatype recvtype , MPI_Comm comm );
int HIPO_WIN_API MPI_Allgatherv_init_c ( const void * sendbuf , MPI_Count sendcount , MPI_Datatype sendtype , void * recvbuf , const MPI_Count recvcounts [ ] , const MPI_Aint displs [ ] , MPI_Datatype recvtype , MPI_Comm comm , MPI_Info info , MPI_Request * request );
int HIPO_WIN_API MPI_Allreduce_c ( const void * sendbuf , void * recvbuf , MPI_Count count , MPI_Datatype datatype , MPI_Op op , MPI_Comm comm );
int HIPO_WIN_API MPI_Allreduce_init_c ( const void * sendbuf , void * recvbuf , MPI_Count count , MPI_Datatype datatype , MPI_Op op , MPI_Comm comm , MPI_Info info , MPI_Request * request );
int HIPO_WIN_API MPI_Alltoall_c ( const void * sendbuf , MPI_Count sendcount , MPI_Datatype sendtype , void * recvbuf , MPI_Count recvcount , MPI_Datatype recvtype , MPI_Comm comm );
int HIPO_WIN_API MPI_Alltoall_init_c ( const void * sendbuf , MPI_Count sendcount , MPI_Datatype sendtype , void * recvbuf , MPI_Count recvcount , MPI_Datatype recvtype , MPI_Comm comm , MPI_Info info , MPI_Request * request );
int HIPO_WIN_API MPI_Alltoallv_c ( const void * sendbuf , const MPI_Count sendcounts [ ] , const MPI_Aint sdispls [ ] , MPI_Datatype sendtype , void * recvbuf , const MPI_Count recvcounts [ ] , const MPI_Aint rdispls [ ] , MPI_Datatype recvtype , MPI_Comm comm );
int HIPO_WIN_API MPI_Alltoallv_init_c ( const void * sendbuf , const MPI_Count sendcounts [ ] , const MPI_Aint sdispls [ ] , MPI_Datatype sendtype , void * recvbuf , const MPI_Count recvcounts [ ] , const MPI_Aint rdispls [ ] , MPI_Datatype recvtype , MPI_Comm comm , MPI_Info info , MPI_Request * request );
int HIPO_WIN_API MPI_Alltoallw_c ( const void * sendbuf , const MPI_Count sendcounts [ ] , const MPI_Aint sdispls [ ] , const MPI_Datatype sendtypes [ ] , void * recvbuf , const MPI_Count recvcounts [ ] , const MPI_Aint rdispls [ ] , const MPI_Datatype recvtypes [ ] , MPI_Comm comm );
int HIPO_WIN_API MPI_Alltoallw_init_c ( const void * sendbuf , const MPI_Count sendcounts [ ] , const MPI_Aint sdispls [ ] , const MPI_Datatype sendtypes [ ] , void * recvbuf , const MPI_Count recvcounts [ ] , const MPI_Aint rdispls [ ] , const MPI_Datatype recvtypes [ ] , MPI_Comm comm , MPI_Info info , MPI_Request * request );
int HIPO_WIN_API MPI_Bcast_c ( void * buffer , MPI_Count count , MPI_Datatype datatype , int root , MPI_Comm comm );
int HIPO_WIN_API MPI_Bcast_init_c ( void * buffer , MPI_Count count , MPI_Datatype datatype , int root , MPI_Comm comm , MPI_Info info , MPI_Request * request );
int HIPO_WIN_API MPI_Exscan_c ( const void * sendbuf , void * recvbuf , MPI_Count count , MPI_Datatype datatype , MPI_Op op , MPI_Comm comm );
int HIPO_WIN_API MPI_Exscan_init_c ( const void * sendbuf , void * recvbuf , MPI_Count count , MPI_Datatype datatype , MPI_Op op , MPI_Comm comm , MPI_Info info , MPI_Request * request );
int HIPO_WIN_API MPI_Gather_c ( const void * sendbuf , MPI_Count sendcount , MPI_Datatype sendtype , void * recvbuf , MPI_Count recvcount , MPI_Datatype recvtype , int root , MPI_Comm comm );
int HIPO_WIN_API MPI_Gather_init_c ( const void * sendbuf , MPI_Count sendcount , MPI_Datatype sendtype , void * recvbuf , MPI_Count recvcount , MPI_Datatype recvtype , int root , MPI_Comm comm , MPI_Info info , MPI_Request * request );
int HIPO_WIN_API MPI_Gatherv_c ( const void * sendbuf , MPI_Count sendcount , MPI_Datatype sendtype , void * recvbuf , const MPI_Count recvcounts [ ] , const MPI_Aint displs [ ] , MPI_Datatype recvtype , int root , MPI_Comm comm );
int HIPO_WIN_API MPI_Gatherv_init_c ( const void * sendbuf , MPI_Count sendcount , MPI_Datatype sendtype , void * recvbuf , const MPI_Count recvcounts [ ] , const MPI_Aint displs [ ] , MPI_Datatype recvtype , int root , MPI_Comm comm , MPI_Info info , MPI_Request * request );
int HIPO_WIN_API MPI_Iallgather_c ( const void * sendbuf , MPI_Count sendcount , MPI_Datatype sendtype , void * recvbuf , MPI_Count recvcount , MPI_Datatype recvtype , MPI_Comm comm , MPI_Request * request );
int HIPO_WIN_API MPI_Iallgatherv_c ( const void * sendbuf , MPI_Count sendcount , MPI_Datatype sendtype , void * recvbuf , const MPI_Count recvcounts [ ] , const MPI_Aint displs [ ] , MPI_Datatype recvtype , MPI_Comm comm , MPI_Request * request );
int HIPO_WIN_API MPI_Iallreduce_c ( const void * sendbuf , void * recvbuf , MPI_Count count , MPI_Datatype datatype , MPI_Op op , MPI_Comm comm , MPI_Request * request );
int HIPO_WIN_API MPI_Ialltoall_c ( const void * sendbuf , MPI_Count sendcount , MPI_Datatype sendtype , void * recvbuf , MPI_Count recvcount , MPI_Datatype recvtype , MPI_Comm comm , MPI_Request * request );
int HIPO_WIN_API MPI_Ialltoallv_c ( const void * sendbuf , const MPI_Count sendcounts [ ] , const MPI_Aint sdispls [ ] , MPI_Datatype sendtype , void * recvbuf , const MPI_Count recvcounts [ ] , const MPI_Aint rdispls [ ] , MPI_Datatype recvtype , MPI_Comm comm , MPI_Request * request );
int HIPO_WIN_API MPI_Ialltoallw_c ( const void * sendbuf , const MPI_Count sendcounts [ ] , const MPI_Aint sdispls [ ] , const MPI_Datatype sendtypes [ ] , void * recvbuf , const MPI_Count recvcounts [ ] , const MPI_Aint rdispls [ ] , const MPI_Datatype recvtypes [ ] , MPI_Comm comm , MPI_Request * request );
int HIPO_WIN_API MPI_Ibcast_c ( void * buffer , MPI_Count count , MPI_Datatype datatype , int root , MPI_Comm comm , MPI_Request * request );
int HIPO_WIN_API MPI_Iexscan_c ( const void * sendbuf , void * recvbuf , MPI_Count count , MPI_Datatype datatype , MPI_Op op , MPI_Comm comm , MPI_Request * request );
int HIPO_WIN_API MPI_Igather_c ( const void * sendbuf , MPI_Count sendcount , MPI_Datatype sendtype , void * recvbuf , MPI_Count recvcount , MPI_Datatype recvtype , int root , MPI_Comm comm , MPI_Request * request );
int HIPO_WIN_API MPI_Igatherv_c ( const void * sendbuf , MPI_Count sendcount , MPI_Datatype sendtype , void * recvbuf , const MPI_Count recvcounts [ ] , const MPI_Aint displs [ ] , MPI_Datatype recvtype , int root , MPI_Comm comm , MPI_Request * request );
int HIPO_WIN_API MPI_Ineighbor_allgather_c ( const void * sendbuf , MPI_Count sendcount , MPI_Datatype sendtype , void * recvbuf , MPI_Count recvcount , MPI_Datatype recvtype , MPI_Comm comm , MPI_Request * request );
int HIPO_WIN_API MPI_Ineighbor_allgatherv_c ( const void * sendbuf , MPI_Count sendcount , MPI_Datatype sendtype , void * recvbuf , const MPI_Count recvcounts [ ] , const MPI_Aint displs [ ] , MPI_Datatype recvtype , MPI_Comm comm , MPI_Request * request );
int HIPO_WIN_API MPI_Ineighbor_alltoall_c ( const void * sendbuf , MPI_Count sendcount , MPI_Datatype sendtype , void * recvbuf , MPI_Count recvcount , MPI_Datatype recvtype , MPI_Comm comm , MPI_Request * request );
int HIPO_WIN_API MPI_Ineighbor_alltoallv_c ( const void * sendbuf , const MPI_Count sendcounts [ ] , const MPI_Aint sdispls [ ] , MPI_Datatype sendtype , void * recvbuf , const MPI_Count recvcounts [ ] , const MPI_Aint rdispls [ ] , MPI_Datatype recvtype , MPI_Comm comm , MPI_Request * request );
int HIPO_WIN_API MPI_Ineighbor_alltoallw_c ( const void * sendbuf , const MPI_Count sendcounts [ ] , const MPI_Aint sdispls [ ] , const MPI_Datatype sendtypes [ ] , void * recvbuf , const MPI_Count recvcounts [ ] , const MPI_Aint rdispls [ ] , const MPI_Datatype recvtypes [ ] , MPI_Comm comm , MPI_Request * request );
int HIPO_WIN_API MPI_Ireduce_c ( const void * sendbuf , void * recvbuf , MPI_Count count , MPI_Datatype datatype , MPI_Op op , int root , MPI_Comm comm , MPI_Request * request );
int HIPO_WIN_API MPI_Ireduce_scatter_c ( const void * sendbuf , void * recvbuf , const MPI_Count recvcounts [ ] , MPI_Datatype datatype , MPI_Op op , MPI_Comm comm , MPI_Request * request );
int HIPO_WIN_API MPI_Ireduce_scatter_block_c ( const void * sendbuf , void * recvbuf , MPI_Count recvcount , MPI_Datatype datatype , MPI_Op op , MPI_Comm comm , MPI_Request * request );
int HIPO_WIN_API MPI_Iscan_c ( const void * sendbuf , void * recvbuf , MPI_Count count , MPI_Datatype datatype , MPI_Op op , MPI_Comm comm , MPI_Request * request );
int HIPO_WIN_API MPI_Iscatter_c ( const void * sendbuf , MPI_Count sendcount , MPI_Datatype sendtype , void * recvbuf , MPI_Count recvcount , MPI_Datatype recvtype , int root , MPI_Comm comm , MPI_Request * request );
int HIPO_WIN_API MPI_Iscatterv_c ( const void * sendbuf , const MPI_Count sendcounts [ ] , const MPI_Aint displs [ ] , MPI_Datatype sendtype , void * recvbuf , MPI_Count recvcount , MPI_Datatype recvtype , int root , MPI_Comm comm , MPI_Request * request );
int HIPO_WIN_API MPI_Neighbor_allgather_c ( const void * sendbuf , MPI_Count sendcount , MPI_Datatype sendtype , void * recvbuf , MPI_Count recvcount , MPI_Datatype recvtype , MPI_Comm comm );
int HIPO_WIN_API MPI_Neighbor_allgather_init_c ( const void * sendbuf , MPI_Count sendcount , MPI_Datatype sendtype , void * recvbuf , MPI_Count recvcount , MPI_Datatype recvtype , MPI_Comm comm , MPI_Info info , MPI_Request * request );
int HIPO_WIN_API MPI_Neighbor_allgatherv_c ( const void * sendbuf , MPI_Count sendcount , MPI_Datatype sendtype , void * recvbuf , const MPI_Count recvcounts [ ] , const MPI_Aint displs [ ] , MPI_Datatype recvtype , MPI_Comm comm );
int HIPO_WIN_API MPI_Neighbor_allgatherv_init_c ( const void * sendbuf , MPI_Count sendcount , MPI_Datatype sendtype , void * recvbuf , const MPI_Count recvcounts [ ] , const MPI_Aint displs [ ] , MPI_Datatype recvtype , MPI_Comm comm , MPI_Info info , MPI_Request * request );
int HIPO_WIN_API MPI_Neighbor_alltoall_c ( const void * sendbuf , MPI_Count sendcount , MPI_Datatype sendtype , void * recvbuf , MPI_Count recvcount , MPI_Datatype recvtype , MPI_Comm comm );
int HIPO_WIN_API MPI_Neighbor_alltoall_init_c ( const void * sendbuf , MPI_Count sendcount , MPI_Datatype sendtype , void * recvbuf , MPI_Count recvcount , MPI_Datatype recvtype , MPI_Comm comm , MPI_Info info , MPI_Request * request );
int HIPO_WIN_API MPI_Neighbor_alltoallv_c ( const void * sendbuf , const MPI_Count sendcounts [ ] , const MPI_Aint sdispls [ ] , MPI_Datatype sendtype , void * recvbuf , const MPI_Count recvcounts [ ] , const MPI_Aint rdispls [ ] , MPI_Datatype recvtype , MPI_Comm comm );
int HIPO_WIN_API MPI_Neighbor_alltoallv_init_c ( const void * sendbuf , const MPI_Count sendcounts [ ] , const MPI_Aint sdispls [ ] , MPI_Datatype sendtype , void * recvbuf , const MPI_Count recvcounts [ ] , const MPI_Aint rdispls [ ] , MPI_Datatype recvtype , MPI_Comm comm , MPI_Info info , MPI_Request * request );
int HIPO_WIN_API MPI_Neighbor_alltoallw_c ( const void * sendbuf , const MPI_Count sendcounts [ ] , const MPI_Aint sdispls [ ] , const MPI_Datatype sendtypes [ ] , void * recvbuf , const MPI_Count recvcounts [ ] , const MPI_Aint rdispls [ ] , const MPI_Datatype recvtypes [ ] , MPI_Comm comm );
int HIPO_WIN_API MPI_Neighbor_alltoallw_init_c ( const void * sendbuf , const MPI_Count sendcounts [ ] , const MPI_Aint sdispls [ ] , const MPI_Datatype sendtypes [ ] , void * recvbuf , const MPI_Count recvcounts [ ] , const MPI_Aint rdispls [ ] , const MPI_Datatype recvtypes [ ] , MPI_Comm comm , MPI_Info info , MPI_Request * request );
int HIPO_WIN_API MPI_Reduce_c ( const void * sendbuf , void * recvbuf , MPI_Count count , MPI_Datatype datatype , MPI_Op op , int root , MPI_Comm comm );
int HIPO_WIN_API MPI_Reduce_init_c ( const void * sendbuf , void * recvbuf , MPI_Count count , MPI_Datatype datatype , MPI_Op op , int root , MPI_Comm comm , MPI_Info info , MPI_Request * request );
int HIPO_WIN_API MPI_Reduce_local_c ( const void * inbuf , void * inoutbuf , MPI_Count count , MPI_Datatype datatype , MPI_Op op );
int HIPO_WIN_API MPI_Reduce_scatter_c ( const void * sendbuf , void * recvbuf , const MPI_Count recvcounts [ ] , MPI_Datatype datatype , MPI_Op op , MPI_Comm comm );
int HIPO_WIN_API MPI_Reduce_scatter_block_c ( const void * sendbuf , void * recvbuf , MPI_Count recvcount , MPI_Datatype datatype , MPI_Op op , MPI_Comm comm );
int HIPO_WIN_API MPI_Reduce_scatter_block_init_c ( const void * sendbuf , void * recvbuf , MPI_Count recvcount , MPI_Datatype datatype , MPI_Op op , MPI_Comm comm , MPI_Info info , MPI_Request * request );
int HIPO_WIN_API MPI_Reduce_scatter_init_c ( const void * sendbuf , void * recvbuf , const MPI_Count recvcounts [ ] , MPI_Datatype datatype , MPI_Op op , MPI_Comm comm , MPI_Info info , MPI_Request * request );
int HIPO_WIN_API MPI_Scan_c ( const void * sendbuf , void * recvbuf , MPI_Count count , MPI_Datatype datatype , MPI_Op op , MPI_Comm comm );
int HIPO_WIN_API MPI_Scan_init_c ( const void * sendbuf , void * recvbuf , MPI_Count count , MPI_Datatype datatype , MPI_Op op , MPI_Comm comm , MPI_Info info , MPI_Request * request );
int HIPO_WIN_API MPI_Scatter_c ( const void * sendbuf , MPI_Count sendcount , MPI_Datatype sendtype , void * recvbuf , MPI_Count recvcount , MPI_Datatype recvtype , int root , MPI_Comm comm );
int HIPO_WIN_API MPI_Scatter_init_c ( const void * sendbuf , MPI_Count sendcount , MPI_Datatype sendtype , void * recvbuf , MPI_Count recvcount , MPI_Datatype recvtype , int root , MPI_Comm comm , MPI_Info info , MPI_Request * request );
int HIPO_WIN_API MPI_Scatterv_c ( const void * sendbuf , const MPI_Count sendcounts [ ] , const MPI_Aint displs [ ] , MPI_Datatype sendtype , void * recvbuf , MPI_Count recvcount , MPI_Datatype recvtype , int root , MPI_Comm comm );
int HIPO_WIN_API MPI_Scatterv_init_c ( const void * sendbuf , const MPI_Count sendcounts [ ] , const MPI_Aint displs [ ] , MPI_Datatype sendtype , void * recvbuf , MPI_Count recvcount , MPI_Datatype recvtype , int root , MPI_Comm comm , MPI_Info info , MPI_Request * request );
int HIPO_WIN_API MPI_Get_count_c ( const MPI_Status * status , MPI_Datatype datatype , MPI_Count * count );
int HIPO_WIN_API MPI_Get_elements_c ( const MPI_Status * status , MPI_Datatype datatype , MPI_Count * count );
int HIPO_WIN_API MPI_Pack_c ( const void * inbuf , MPI_Count incount , MPI_Datatype datatype , void * outbuf , MPI_Count outsize , MPI_Count * position , MPI_Comm comm );
int HIPO_WIN_API MPI_Pack_external_c ( const char * datarep , const void * inbuf , MPI_Count incount , MPI_Datatype datatype , void * outbuf , MPI_Count outsize , MPI_Count * position );
int HIPO_WIN_API MPI_Pack_external_size_c ( const char * datarep , MPI_Count incount , MPI_Datatype datatype , MPI_Count * size );
int HIPO_WIN_API MPI_Pack_size_c ( MPI_Count incount , MPI_Datatype datatype , MPI_Comm comm , MPI_Count * size );
int HIPO_WIN_API MPI_Type_contiguous_c ( MPI_Count count , MPI_Datatype oldtype , MPI_Datatype * newtype );
int HIPO_WIN_API MPI_Type_create_darray_c ( int size , int rank , int ndims , const MPI_Count array_of_gsizes [ ] , const int array_of_distribs [ ] , const int array_of_dargs [ ] , const int array_of_psizes [ ] , int order , MPI_Datatype oldtype , MPI_Datatype * newtype );
int HIPO_WIN_API MPI_Type_create_hindexed_c ( MPI_Count count , const MPI_Count array_of_blocklengths [ ] , const MPI_Count array_of_displacements [ ] , MPI_Datatype oldtype , MPI_Datatype * newtype );
int HIPO_WIN_API MPI_Type_create_hindexed_block_c ( MPI_Count count , MPI_Count blocklength , const MPI_Count array_of_displacements [ ] , MPI_Datatype oldtype , MPI_Datatype * newtype );
int HIPO_WIN_API MPI_Type_create_hvector_c ( MPI_Count count , MPI_Count blocklength , MPI_Count stride , MPI_Datatype oldtype , MPI_Datatype * newtype );
int HIPO_WIN_API MPI_Type_create_indexed_block_c ( MPI_Count count , MPI_Count blocklength , const MPI_Count array_of_displacements [ ] , MPI_Datatype oldtype , MPI_Datatype * newtype );
int HIPO_WIN_API MPI_Type_create_resized_c ( MPI_Datatype oldtype , MPI_Count lb , MPI_Count extent , MPI_Datatype * newtype );
int HIPO_WIN_API MPI_Type_create_struct_c ( MPI_Count count , const MPI_Count array_of_blocklengths [ ] , const MPI_Count array_of_displacements [ ] , const MPI_Datatype array_of_types [ ] , MPI_Datatype * newtype );
int HIPO_WIN_API MPI_Type_create_subarray_c ( int ndims , const MPI_Count array_of_sizes [ ] , const MPI_Count array_of_subsizes [ ] , const MPI_Count array_of_starts [ ] , int order , MPI_Datatype oldtype , MPI_Datatype * newtype );
int HIPO_WIN_API MPI_Type_get_contents_c ( MPI_Datatype datatype , MPI_Count max_integers , MPI_Count max_addresses , MPI_Count max_large_counts , MPI_Count max_datatypes , int array_of_integers [ ] , MPI_Aint array_of_addresses [ ] , MPI_Count array_of_large_counts [ ] , MPI_Datatype array_of_datatypes [ ] );
int HIPO_WIN_API MPI_Type_get_envelope_c ( MPI_Datatype datatype , MPI_Count * num_integers , MPI_Count * num_addresses , MPI_Count * num_large_counts , MPI_Count * num_datatypes , int * combiner );
int HIPO_WIN_API MPI_Type_get_extent_c ( MPI_Datatype datatype , MPI_Count * lb , MPI_Count * extent );
int HIPO_WIN_API MPI_Type_get_true_extent_c ( MPI_Datatype datatype , MPI_Count * true_lb , MPI_Count * true_extent );
int HIPO_WIN_API MPI_Type_indexed_c ( MPI_Count count , const MPI_Count array_of_blocklengths [ ] , const MPI_Count array_of_displacements [ ] , MPI_Datatype oldtype , MPI_Datatype * newtype );
int HIPO_WIN_API MPI_Type_size_c ( MPI_Datatype datatype , MPI_Count * size );
int HIPO_WIN_API MPI_Type_vector_c ( MPI_Count count , MPI_Count blocklength , MPI_Count stride , MPI_Datatype oldtype , MPI_Datatype * newtype );
int HIPO_WIN_API MPI_Unpack_c ( const void * inbuf , MPI_Count insize , MPI_Count * position , void * outbuf , MPI_Count outcount , MPI_Datatype datatype , MPI_Comm comm );
int HIPO_WIN_API MPI_Unpack_external_c ( const char datarep [ ] , const void * inbuf , MPI_Count insize , MPI_Count * position , void * outbuf , MPI_Count outcount , MPI_Datatype datatype );
int HIPO_WIN_API MPI_Op_create_c ( MPI_User_function_c * user_fn , int commute , MPI_Op * op );
int HIPO_WIN_API MPI_Bsend_c ( const void * buf , MPI_Count count , MPI_Datatype datatype , int dest , int tag , MPI_Comm comm );
int HIPO_WIN_API MPI_Bsend_init_c ( const void * buf , MPI_Count count , MPI_Datatype datatype , int dest , int tag , MPI_Comm comm , MPI_Request * request );
int HIPO_WIN_API MPI_Buffer_attach_c ( void * buffer , MPI_Count size );
int HIPO_WIN_API MPI_Buffer_detach_c ( void * buffer_addr , MPI_Count * size );
int HIPO_WIN_API MPI_Ibsend_c ( const void * buf , MPI_Count count , MPI_Datatype datatype , int dest , int tag , MPI_Comm comm , MPI_Request * request );
int HIPO_WIN_API MPI_Imrecv_c ( void * buf , MPI_Count count , MPI_Datatype datatype , MPI_Message * message , MPI_Request * request );
int HIPO_WIN_API MPI_Irecv_c ( void * buf , MPI_Count count , MPI_Datatype datatype , int source , int tag , MPI_Comm comm , MPI_Request * request );
int HIPO_WIN_API MPI_Irsend_c ( const void * buf , MPI_Count count , MPI_Datatype datatype , int dest , int tag , MPI_Comm comm , MPI_Request * request );
int HIPO_WIN_API MPI_Isend_c ( const void * buf , MPI_Count count , MPI_Datatype datatype , int dest , int tag , MPI_Comm comm , MPI_Request * request );
int HIPO_WIN_API MPI_Isendrecv_c ( const void * sendbuf , MPI_Count sendcount , MPI_Datatype sendtype , int dest , int sendtag , void * recvbuf , MPI_Count recvcount , MPI_Datatype recvtype , int source , int recvtag , MPI_Comm comm , MPI_Request * request );
int HIPO_WIN_API MPI_Isendrecv_replace_c ( void * buf , MPI_Count count , MPI_Datatype datatype , int dest , int sendtag , int source , int recvtag , MPI_Comm comm , MPI_Request * request );
int HIPO_WIN_API MPI_Issend_c ( const void * buf , MPI_Count count , MPI_Datatype datatype , int dest , int tag , MPI_Comm comm , MPI_Request * request );
int HIPO_WIN_API MPI_Mrecv_c ( void * buf , MPI_Count count , MPI_Datatype datatype , MPI_Message * message , MPI_Status * status );
int HIPO_WIN_API MPI_Recv_c ( void * buf , MPI_Count count , MPI_Datatype datatype , int source , int tag , MPI_Comm comm , MPI_Status * status );
int HIPO_WIN_API MPI_Recv_init_c ( void * buf , MPI_Count count , MPI_Datatype datatype , int source , int tag , MPI_Comm comm , MPI_Request * request );
int HIPO_WIN_API MPI_Rsend_c ( const void * buf , MPI_Count count , MPI_Datatype datatype , int dest , int tag , MPI_Comm comm );
int HIPO_WIN_API MPI_Rsend_init_c ( const void * buf , MPI_Count count , MPI_Datatype datatype , int dest , int tag , MPI_Comm comm , MPI_Request * request );
int HIPO_WIN_API MPI_Send_c ( const void * buf , MPI_Count count , MPI_Datatype datatype , int dest , int tag , MPI_Comm comm );
int HIPO_WIN_API MPI_Send_init_c ( const void * buf , MPI_Count count , MPI_Datatype datatype , int dest , int tag , MPI_Comm comm , MPI_Request * request );
int HIPO_WIN_API MPI_Sendrecv_c ( const void * sendbuf , MPI_Count sendcount , MPI_Datatype sendtype , int dest , int sendtag , void * recvbuf , MPI_Count recvcount , MPI_Datatype recvtype , int source , int recvtag , MPI_Comm comm , MPI_Status * status );
int HIPO_WIN_API MPI_Sendrecv_replace_c ( void * buf , MPI_Count count , MPI_Datatype datatype , int dest , int sendtag , int source , int recvtag , MPI_Comm comm , MPI_Status * status );
int HIPO_WIN_API MPI_Ssend_c ( const void * buf , MPI_Count count , MPI_Datatype datatype , int dest , int tag , MPI_Comm comm );
int HIPO_WIN_API MPI_Ssend_init_c ( const void * buf , MPI_Count count , MPI_Datatype datatype , int dest , int tag , MPI_Comm comm , MPI_Request * request );
int HIPO_WIN_API MPI_Accumulate_c ( const void * origin_addr , MPI_Count origin_count , MPI_Datatype origin_datatype , int target_rank , MPI_Aint target_disp , MPI_Count target_count , MPI_Datatype target_datatype , MPI_Op op , MPI_Win win );
int HIPO_WIN_API MPI_Get_c ( void * origin_addr , MPI_Count origin_count , MPI_Datatype origin_datatype , int target_rank , MPI_Aint target_disp , MPI_Count target_count , MPI_Datatype target_datatype , MPI_Win win );
int HIPO_WIN_API MPI_Get_accumulate_c ( const void * origin_addr , MPI_Count origin_count , MPI_Datatype origin_datatype , void * result_addr , MPI_Count result_count , MPI_Datatype result_datatype , int target_rank , MPI_Aint target_disp , MPI_Count target_count , MPI_Datatype target_datatype , MPI_Op op , MPI_Win win );
int HIPO_WIN_API MPI_Put_c ( const void * origin_addr , MPI_Count origin_count , MPI_Datatype origin_datatype , int target_rank , MPI_Aint target_disp , MPI_Count target_count , MPI_Datatype target_datatype , MPI_Win win );
int HIPO_WIN_API MPI_Raccumulate_c ( const void * origin_addr , MPI_Count origin_count , MPI_Datatype origin_datatype , int target_rank , MPI_Aint target_disp , MPI_Count target_count , MPI_Datatype target_datatype , MPI_Op op , MPI_Win win , MPI_Request * request );
int HIPO_WIN_API MPI_Rget_c ( void * origin_addr , MPI_Count origin_count , MPI_Datatype origin_datatype , int target_rank , MPI_Aint target_disp , MPI_Count target_count , MPI_Datatype target_datatype , MPI_Win win , MPI_Request * request );
int HIPO_WIN_API MPI_Rget_accumulate_c ( const void * origin_addr , MPI_Count origin_count , MPI_Datatype origin_datatype , void * result_addr , MPI_Count result_count , MPI_Datatype result_datatype , int target_rank , MPI_Aint target_disp , MPI_Count target_count , MPI_Datatype target_datatype , MPI_Op op , MPI_Win win , MPI_Request * request );
int HIPO_WIN_API MPI_Rput_c ( const void * origin_addr , MPI_Count origin_count , MPI_Datatype origin_datatype , int target_rank , MPI_Aint target_disp , MPI_Count target_count , MPI_Datatype target_datatype , MPI_Win win , MPI_Request * request );
int HIPO_WIN_API MPI_Win_allocate_c ( MPI_Aint size , MPI_Aint disp_unit , MPI_Info info , MPI_Comm comm , void * baseptr , MPI_Win * win );
int HIPO_WIN_API MPI_Win_allocate_shared_c ( MPI_Aint size , MPI_Aint disp_unit , MPI_Info info , MPI_Comm comm , void * baseptr , MPI_Win * win );
int HIPO_WIN_API MPI_Win_create_c ( void * base , MPI_Aint size , MPI_Aint disp_unit , MPI_Info info , MPI_Comm comm , MPI_Win * win );
int HIPO_WIN_API MPI_Win_shared_query_c ( MPI_Win win , int rank , MPI_Aint * size , MPI_Aint * disp_unit , void * baseptr );
int HIPO_WIN_API MPI_File_open ( MPI_Comm comm , const char * filename , int amode , MPI_Info info , MPI_File * fh );
int HIPO_WIN_API MPI_File_close ( MPI_File * fh );
int HIPO_WIN_API MPI_File_delete ( const char * filename , MPI_Info info );
int HIPO_WIN_API MPI_File_set_size ( MPI_File fh , MPI_Offset size );
int HIPO_WIN_API MPI_File_preallocate ( MPI_File fh , MPI_Offset size );
int HIPO_WIN_API MPI_File_get_size ( MPI_File fh , MPI_Offset * size );
int HIPO_WIN_API MPI_File_get_group ( MPI_File fh , MPI_Group * group );
int HIPO_WIN_API MPI_File_get_amode ( MPI_File fh , int * amode );
int HIPO_WIN_API MPI_File_set_info ( MPI_File fh , MPI_Info info );
int HIPO_WIN_API MPI_File_get_info ( MPI_File fh , MPI_Info * info_used );
int HIPO_WIN_API MPI_File_set_view ( MPI_File fh , MPI_Offset disp , MPI_Datatype etype , MPI_Datatype filetype , const char * datarep , MPI_Info info );
int HIPO_WIN_API MPI_File_get_view ( MPI_File fh , MPI_Offset * disp , MPI_Datatype * etype , MPI_Datatype * filetype , char * datarep );
int HIPO_WIN_API MPI_File_read_at ( MPI_File fh , MPI_Offset offset , void * buf , int count , MPI_Datatype datatype , MPI_Status * status );
int HIPO_WIN_API MPI_File_read_at_all ( MPI_File fh , MPI_Offset offset , void * buf , int count , MPI_Datatype datatype , MPI_Status * status );
int HIPO_WIN_API MPI_File_write_at ( MPI_File fh , MPI_Offset offset , const void * buf , int count , MPI_Datatype datatype , MPI_Status * status );
int HIPO_WIN_API MPI_File_write_at_all ( MPI_File fh , MPI_Offset offset , const void * buf , int count , MPI_Datatype datatype , MPI_Status * status );
int HIPO_WIN_API MPI_File_iread_at ( MPI_File fh , MPI_Offset offset , void * buf , int count , MPI_Datatype datatype , MPIO_Request * request );
int HIPO_WIN_API MPI_File_iwrite_at ( MPI_File fh , MPI_Offset offset , const void * buf , int count , MPI_Datatype datatype , MPIO_Request * request );
int HIPO_WIN_API MPI_File_read ( MPI_File fh , void * buf , int count , MPI_Datatype datatype , MPI_Status * status );
int HIPO_WIN_API MPI_File_read_all ( MPI_File fh , void * buf , int count , MPI_Datatype datatype , MPI_Status * status );
int HIPO_WIN_API MPI_File_write ( MPI_File fh , const void * buf , int count , MPI_Datatype datatype , MPI_Status * status );
int HIPO_WIN_API MPI_File_write_all ( MPI_File fh , const void * buf , int count , MPI_Datatype datatype , MPI_Status * status );
int HIPO_WIN_API MPI_File_iread ( MPI_File fh , void * buf , int count , MPI_Datatype datatype , MPIO_Request * request );
int HIPO_WIN_API MPI_File_iwrite ( MPI_File fh , const void * buf , int count , MPI_Datatype datatype , MPIO_Request * request );
int HIPO_WIN_API MPI_File_seek ( MPI_File fh , MPI_Offset offset , int whence );
int HIPO_WIN_API MPI_File_get_position ( MPI_File fh , MPI_Offset * offset );
int HIPO_WIN_API MPI_File_get_byte_offset ( MPI_File fh , MPI_Offset offset , MPI_Offset * disp );
int HIPO_WIN_API MPI_File_read_shared ( MPI_File fh , void * buf , int count , MPI_Datatype datatype , MPI_Status * status );
int HIPO_WIN_API MPI_File_write_shared ( MPI_File fh , const void * buf , int count , MPI_Datatype datatype , MPI_Status * status );
int HIPO_WIN_API MPI_File_iread_shared ( MPI_File fh , void * buf , int count , MPI_Datatype datatype , MPIO_Request * request );
int HIPO_WIN_API MPI_File_iwrite_shared ( MPI_File fh , const void * buf , int count , MPI_Datatype datatype , MPIO_Request * request );
int HIPO_WIN_API MPI_File_read_ordered ( MPI_File fh , void * buf , int count , MPI_Datatype datatype , MPI_Status * status );
int HIPO_WIN_API MPI_File_write_ordered ( MPI_File fh , const void * buf , int count , MPI_Datatype datatype , MPI_Status * status );
int HIPO_WIN_API MPI_File_seek_shared ( MPI_File fh , MPI_Offset offset , int whence );
int HIPO_WIN_API MPI_File_get_position_shared ( MPI_File fh , MPI_Offset * offset );
int HIPO_WIN_API MPI_File_read_at_all_begin ( MPI_File fh , MPI_Offset offset , void * buf , int count , MPI_Datatype datatype );
int HIPO_WIN_API MPI_File_read_at_all_end ( MPI_File fh , void * buf , MPI_Status * status );
int HIPO_WIN_API MPI_File_write_at_all_begin ( MPI_File fh , MPI_Offset offset , const void * buf , int count , MPI_Datatype datatype );
int HIPO_WIN_API MPI_File_write_at_all_end ( MPI_File fh , const void * buf , MPI_Status * status );
int HIPO_WIN_API MPI_File_read_all_begin ( MPI_File fh , void * buf , int count , MPI_Datatype datatype );
int HIPO_WIN_API MPI_File_read_all_end ( MPI_File fh , void * buf , MPI_Status * status );
int HIPO_WIN_API MPI_File_write_all_begin ( MPI_File fh , const void * buf , int count , MPI_Datatype datatype );
int HIPO_WIN_API MPI_File_write_all_end ( MPI_File fh , const void * buf , MPI_Status * status );
int HIPO_WIN_API MPI_File_read_ordered_begin ( MPI_File fh , void * buf , int count , MPI_Datatype datatype );
int HIPO_WIN_API MPI_File_read_ordered_end ( MPI_File fh , void * buf , MPI_Status * status );
int HIPO_WIN_API MPI_File_write_ordered_begin ( MPI_File fh , const void * buf , int count , MPI_Datatype datatype );
int HIPO_WIN_API MPI_File_write_ordered_end ( MPI_File fh , const void * buf , MPI_Status * status );
int HIPO_WIN_API MPI_File_get_type_extent ( MPI_File fh , MPI_Datatype datatype , MPI_Aint * extent );
int HIPO_WIN_API MPI_Register_datarep ( const char * datarep , MPI_Datarep_conversion_function * read_conversion_fn , MPI_Datarep_conversion_function * write_conversion_fn , MPI_Datarep_extent_function * dtype_file_extent_fn , void * extra_state );
int HIPO_WIN_API MPI_File_set_atomicity ( MPI_File fh , int flag );
int HIPO_WIN_API MPI_File_get_atomicity ( MPI_File fh , int * flag );
int HIPO_WIN_API MPI_File_sync ( MPI_File fh );
int HIPO_WIN_API MPI_File_iread_at_all ( MPI_File fh , MPI_Offset offset , void * buf , int count , MPI_Datatype datatype , MPI_Request * request );
int HIPO_WIN_API MPI_File_iwrite_at_all ( MPI_File fh , MPI_Offset offset , const void * buf , int count , MPI_Datatype datatype , MPI_Request * request );
int HIPO_WIN_API MPI_File_iread_all ( MPI_File fh , void * buf , int count , MPI_Datatype datatype , MPI_Request * request );
int HIPO_WIN_API MPI_File_iwrite_all ( MPI_File fh , const void * buf , int count , MPI_Datatype datatype , MPI_Request * request );
int HIPO_WIN_API MPI_File_read_c ( MPI_File fh , void * buf , MPI_Count count , MPI_Datatype datatype , MPI_Status * status );
int HIPO_WIN_API MPI_File_read_all_c ( MPI_File fh , void * buf , MPI_Count count , MPI_Datatype datatype , MPI_Status * status );
int HIPO_WIN_API MPI_File_read_all_begin_c ( MPI_File fh , void * buf , MPI_Count count , MPI_Datatype datatype );
int HIPO_WIN_API MPI_File_read_at_c ( MPI_File fh , MPI_Offset offset , void * buf , MPI_Count count , MPI_Datatype datatype , MPI_Status * status );
int HIPO_WIN_API MPI_File_read_at_all_c ( MPI_File fh , MPI_Offset offset , void * buf , MPI_Count count , MPI_Datatype datatype , MPI_Status * status );
int HIPO_WIN_API MPI_File_read_at_all_begin_c ( MPI_File fh , MPI_Offset offset , void * buf , MPI_Count count , MPI_Datatype datatype );
int HIPO_WIN_API MPI_File_read_ordered_c ( MPI_File fh , void * buf , MPI_Count count , MPI_Datatype datatype , MPI_Status * status );
int HIPO_WIN_API MPI_File_read_ordered_begin_c ( MPI_File fh , void * buf , MPI_Count count , MPI_Datatype datatype );
int HIPO_WIN_API MPI_File_read_shared_c ( MPI_File fh , void * buf , MPI_Count count , MPI_Datatype datatype , MPI_Status * status );
int HIPO_WIN_API MPI_File_write_c ( MPI_File fh , const void * buf , MPI_Count count , MPI_Datatype datatype , MPI_Status * status );
int HIPO_WIN_API MPI_File_write_all_c ( MPI_File fh , const void * buf , MPI_Count count , MPI_Datatype datatype , MPI_Status * status );
int HIPO_WIN_API MPI_File_write_all_begin_c ( MPI_File fh , const void * buf , MPI_Count count , MPI_Datatype datatype );
int HIPO_WIN_API MPI_File_write_at_c ( MPI_File fh , MPI_Offset offset , const void * buf , MPI_Count count , MPI_Datatype datatype , MPI_Status * status );
int HIPO_WIN_API MPI_File_write_at_all_c ( MPI_File fh , MPI_Offset offset , const void * buf , MPI_Count count , MPI_Datatype datatype , MPI_Status * status );
int HIPO_WIN_API MPI_File_write_at_all_begin_c ( MPI_File fh , MPI_Offset offset , const void * buf , MPI_Count count , MPI_Datatype datatype );
int HIPO_WIN_API MPI_File_write_ordered_c ( MPI_File fh , const void * buf , MPI_Count count , MPI_Datatype datatype , MPI_Status * status );
int HIPO_WIN_API MPI_File_write_ordered_begin_c ( MPI_File fh , const void * buf , MPI_Count count , MPI_Datatype datatype );
int HIPO_WIN_API MPI_File_write_shared_c ( MPI_File fh , const void * buf , MPI_Count count , MPI_Datatype datatype , MPI_Status * status );
int HIPO_WIN_API MPI_File_iread_c ( MPI_File fh , void * buf , MPI_Count count , MPI_Datatype datatype , MPIO_Request * request );
int HIPO_WIN_API MPI_File_iread_all_c ( MPI_File fh , void * buf , MPI_Count count , MPI_Datatype datatype , MPI_Request * request );
int HIPO_WIN_API MPI_File_iread_at_c ( MPI_File fh , MPI_Offset offset , void * buf , MPI_Count count , MPI_Datatype datatype , MPIO_Request * request );
int HIPO_WIN_API MPI_File_iread_at_all_c ( MPI_File fh , MPI_Offset offset , void * buf , MPI_Count count , MPI_Datatype datatype , MPI_Request * request );
int HIPO_WIN_API MPI_File_iread_shared_c ( MPI_File fh , void * buf , MPI_Count count , MPI_Datatype datatype , MPIO_Request * request );
int HIPO_WIN_API MPI_File_iwrite_c ( MPI_File fh , const void * buf , MPI_Count count , MPI_Datatype datatype , MPIO_Request * request );
int HIPO_WIN_API MPI_File_iwrite_all_c ( MPI_File fh , const void * buf , MPI_Count count , MPI_Datatype datatype , MPI_Request * request );
int HIPO_WIN_API MPI_File_iwrite_at_c ( MPI_File fh , MPI_Offset offset , const void * buf , MPI_Count count , MPI_Datatype datatype , MPIO_Request * request );
int HIPO_WIN_API MPI_File_iwrite_at_all_c ( MPI_File fh , MPI_Offset offset , const void * buf , MPI_Count count , MPI_Datatype datatype , MPI_Request * request );
int HIPO_WIN_API MPI_File_iwrite_shared_c ( MPI_File fh , const void * buf , MPI_Count count , MPI_Datatype datatype , MPIO_Request * request );
int HIPO_WIN_API MPI_File_get_type_extent_c ( MPI_File fh , MPI_Datatype datatype , MPI_Count * extent );
int HIPO_WIN_API MPI_Register_datarep_c ( const char * datarep , MPI_Datarep_conversion_function_c * read_conversion_fn , MPI_Datarep_conversion_function_c * write_conversion_fn , MPI_Datarep_extent_function * dtype_file_extent_fn , void * extra_state );
MPI_File HIPO_WIN_API MPI_File_f2c ( MPI_Fint file );
MPI_Fint HIPO_WIN_API MPI_File_c2f ( MPI_File file );

#ifdef __cplusplus
}
#endif
