#ifndef MT_WRAPPER_H
#define MT_WRAPPER_H

#include "merkle-tree/src/merkletree.h"

typedef struct mt_obj
{
  mt_t *mt;
  uint32_t num_blocks;
  int write;
} mt_obj;

#endif /* MT_WRAPPER_H */