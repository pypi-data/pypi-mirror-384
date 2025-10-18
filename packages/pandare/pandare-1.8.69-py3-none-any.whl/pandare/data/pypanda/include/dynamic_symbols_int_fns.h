#define MAX_PATH_LEN 256

struct symbol {
    target_ulong address;
    target_ulong value;
    int symtab_idx;
    int  reloc_type;
    char name[MAX_PATH_LEN]; 
    char section[MAX_PATH_LEN]; 
};

struct hook_symbol_resolve;

typedef void (*dynamic_hook_func_t)(struct hook_symbol_resolve *, struct symbol, target_ulong asid);

struct hook_symbol_resolve{
    char name[MAX_PATH_LEN];
    target_ulong offset;
    bool hook_offset;
    char section[MAX_PATH_LEN];
    dynamic_hook_func_t cb;
    bool enabled;
    int id;
};

struct symbol resolve_symbol(CPUState* cpu, target_ulong asid, char* section_name, char* symbol);
void hook_symbol_resolution(struct hook_symbol_resolve *h);
struct symbol get_best_matching_symbol(CPUState* cpu, target_ulong address, target_ulong asid);



