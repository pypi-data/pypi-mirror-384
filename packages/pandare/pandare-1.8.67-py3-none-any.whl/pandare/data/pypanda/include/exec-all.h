
void cpu_gen_init(void);
bool cpu_restore_state(CPUState *cpu, uintptr_t searched_pc);

void cpu_loop_exit_noexc(CPUState *cpu);
void cpu_io_recompile(CPUState *cpu, uintptr_t retaddr);
TranslationBlock *tb_gen_code(CPUState *cpu,
                              target_ulong pc, target_ulong cs_base,
                              uint32_t flags,
                              int cflags);

void cpu_loop_exit(CPUState *cpu);
void cpu_loop_exit_restore(CPUState *cpu, uintptr_t pc);
void cpu_loop_exit_atomic(CPUState *cpu, uintptr_t pc);
