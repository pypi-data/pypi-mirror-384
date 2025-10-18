
/** @brief Memory types. */
typedef enum { RR_MEM_IO, RR_MEM_RAM, RR_MEM_UNKNOWN } RR_mem_type;

/**
 * @brief Record/Replay modes. Also used to request transitions from one
 * mode to another.
 */
typedef enum { RR_NOCHANGE=-1, RR_OFF=0, RR_RECORD, RR_REPLAY } RR_mode;

/** @brief Return codes for functions controlling record/replay. */
typedef enum { 
    RRCTRL_EINVALID=-2, /* invalid mode transition requested */
    RRCTRL_EPENDING=-1, /* another transition is already pending */
    RRCTRL_OK=0         /* transition request registered */
} RRCTRL_ret;

