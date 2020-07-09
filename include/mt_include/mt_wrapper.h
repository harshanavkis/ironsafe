#ifndef MT_WRAPPER_H
#define MT_WRAPPER_H

#include "merkletree.h"

typedef struct mt_obj
{
  mt_t *mt;
  uint32_t num_blocks;
  int write;
} mt_obj;

uint32_t num_pages_decrypted;

#endif /* MT_WRAPPER_H */