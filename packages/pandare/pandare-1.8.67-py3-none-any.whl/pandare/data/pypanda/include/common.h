
void panda_cleanup(void);
void panda_set_os_name(char *os_name);
void panda_before_find_fast(void);
void panda_disas(FILE *out, void *code, unsigned long size);
void panda_break_main_loop(void);
MemoryRegion* panda_find_ram(void);
    
extern bool panda_exit_loop;
extern bool panda_break_vl_loop_req;


/**
 * panda_current_asid() - Obtain guest ASID.
 * @env: Pointer to cpu state.
 * 
 * This function figures out and returns the ASID (address space
 * identifier) for a number of archiectures (e.g., cr3 for x86). In
 * many cases, this can be used to distinguish between processes.
 * 
 * Return: A guest pointer is returned, the ASID.
*/
target_ulong panda_current_asid(CPUState *env);
    
/**
 * panda_current_pc() - Get current program counter.
 * @cpu: Cpu state.
 *
 * Note that Qemu typically only updates the pc after executing each
 * basic block of code. If you want this value to be more accurate,
 * you will have to call panda_enable_precise_pc.
 * 
 * Return: Program counter is returned.
 */
target_ulong panda_current_pc(CPUState *cpu);

