#ifndef MT_SERIALIZE_H
#define MT_SERIALIZE_H

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include "mt_wrapper.h"

int serialize_mt(char **dest, mt_t *mt);
void deserialize_init_mt(char *f_path, mt_obj *tree);

#endif /* MT_SERIALIZE_H */