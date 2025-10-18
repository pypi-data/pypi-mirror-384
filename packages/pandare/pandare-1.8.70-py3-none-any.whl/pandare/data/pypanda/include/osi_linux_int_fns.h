
// returns fd for a filename or a NULL if failed
char *osi_linux_fd_to_filename(CPUState *env, OsiProc *p, int fd);

// VMI to get physical address
target_ulong walk_page_table(CPUState *cpu, target_ulong virtual_address);

// returns pos in a file 
unsigned long long osi_linux_fd_to_pos(CPUState *env, OsiProc *p, int fd);

target_ptr_t ext_get_file_struct_ptr(CPUState *env, target_ptr_t task_struct, int fd);
target_ptr_t ext_get_file_dentry(CPUState *env, target_ptr_t file_struct);
target_ulong osi_linux_virt_to_phys(CPUState *cpu, target_ulong addr);
int osi_linux_virtual_memory_read(CPUState *cpu, target_ulong addr, uint8_t *buf, int len);
int osi_linux_virtual_memory_write(CPUState *cpu, target_ulong addr, uint8_t *buf, int len);

