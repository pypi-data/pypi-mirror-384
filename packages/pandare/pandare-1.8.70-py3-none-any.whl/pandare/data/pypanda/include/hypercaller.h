
typedef void (*hypercall_t)(CPUState *cpu);
typedef void (*register_hypercall_t)(uint32_t, hypercall_t);
void register_hypercall(uint32_t magic, hypercall_t);
void unregister_hypercall(uint32_t magic);

