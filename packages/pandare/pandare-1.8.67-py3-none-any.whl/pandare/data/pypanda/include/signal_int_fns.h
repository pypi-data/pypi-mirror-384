
    // Block a signal for all processes
    void block_sig(int32_t sig);

    // Block a signal only for a named process
    void block_sig_by_proc(int32_t sig, char* proc_name);

