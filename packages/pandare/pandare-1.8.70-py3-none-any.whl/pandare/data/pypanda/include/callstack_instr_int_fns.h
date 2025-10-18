
// Public interface

// Get up to n callers from the given stack in use at this moment
// Callers are returned in callers[], most recent first
uint32_t get_callers(target_ulong *callers, uint32_t n, CPUState *cpu);

// Get up to n functions from the given stack in use at this moment
// Functions are returned in functions[], most recent first
uint32_t get_functions(target_ulong *functions, uint32_t n, CPUState *cpu);

// Get up to n binaries from the given stack in use at this moment
// Binaries are returned in libs[], most recent first
uint32_t get_binaries(char **libs, uint32_t n, CPUState *cpu);

// Called by plugins that intend to call get_binaries.
void callstack_enable_binary_tracking(void);

