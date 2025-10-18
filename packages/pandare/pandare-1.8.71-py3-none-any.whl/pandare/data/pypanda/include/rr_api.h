
int panda_vm_quit(void);
int panda_record_begin(const char *name, const char *snapshot);
int panda_record_end(void);
int panda_replay_begin(const char *name);
int panda_replay_end(void);

