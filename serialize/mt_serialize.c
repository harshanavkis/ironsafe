#include "mt_serialize.h"

static unsigned int next_power_two(unsigned int n)
{
	n--; 
  n |= n >> 1; 
  n |= n >> 2; 
  n |= n >> 4; 
  n |= n >> 8; 
  n |= n >> 16; 
  n++; 
  return n;
}

int serialize_mt(char **dest, mt_t *mt)
{
	int num_bytes = 0;
	char *buffer_ptr;

	/* mt->elems: number of blocks protected by this tree */
	num_bytes += sizeof(mt->elems);
	for(int i=0; i<TREE_LEVELS; i++)
	{
		num_bytes += sizeof(mt->level[i]->elems);
		num_bytes += (mt->level[i]->elems)*HASH_LENGTH; // total number of bytes in hash
	}

	num_bytes += sizeof(int);

	(*dest) = (char*) malloc(num_bytes*sizeof(char));

	buffer_ptr = (*dest);

	memcpy(buffer_ptr, &num_bytes, sizeof(int));
	buffer_ptr += sizeof(int);

	memcpy(buffer_ptr, &(mt->elems), sizeof(mt->elems));
	buffer_ptr += sizeof(mt->elems);

	for(int i=0; i<TREE_LEVELS; i++)
	{
		memcpy(buffer_ptr, &(mt->level[i]->elems), sizeof(mt->level[i]->elems));
		buffer_ptr += sizeof(mt->level[i]->elems);

		memcpy(buffer_ptr, mt->level[i]->store, (mt->level[i]->elems)*HASH_LENGTH);
		buffer_ptr += (mt->level[i]->elems)*HASH_LENGTH;
	}

	return num_bytes;
}

void deserialize_init_mt(char *f_path, mt_obj *tree)
{
	/* while deserializing make sure that the number of mt_al elements is power of 2 */
  FILE *fileptr;
	char *buffer, *buf_ptr;
	long filelen;

	/* open file and get its size */
	fileptr = fopen(f_path, "rb"); 
	fseek(fileptr, 0, SEEK_END);          
	filelen = ftell(fileptr);            
	rewind(fileptr);

	/* alloc memory for the file data */
	buffer = (char*) malloc(filelen * sizeof(char));
	fread(buffer, filelen, 1, fileptr);
	fclose(fileptr);

	tree->mt    = mt_create();
	tree->write = 0;
	tree->num_blocks = 0;

	buf_ptr = (char *)buffer;

	/* num_bytes */
	tree->num_blocks = *((int*)buf_ptr);
	buf_ptr += sizeof(int);

	/* mt->elems */
	// memcpy(&(tree->mt->elems), buffer, sizeof(tree->mt->elems));
	tree->mt->elems = *((int*) buffer);
	buf_ptr += sizeof(tree->mt->elems);

	for (int i=0; i<TREE_LEVELS; i++)
	{
		tree->mt->level[i] = (mt_al_t*) malloc(sizeof(mt_al_t));

		/* number of elements in mt array list */
		// memcpy(&(tree->mt->level[i]->elems), buf_ptr, sizeof(tree->mt->level[i]->elems));
		tree->mt->level[i]->elems = *((uint32_t*)buf_ptr);
		buf_ptr += sizeof(tree->mt->level[i]->elems);

		/* hash values in the mt array list */
		unsigned int store_size = next_power_two(tree->mt->level[i]->elems);
		tree->mt->level[i]->store = (uint8_t*) malloc(store_size*HASH_LENGTH*sizeof(uint8_t));
		memcpy(tree->mt->level[i]->store, buf_ptr, (tree->mt->level[i]->elems)*HASH_LENGTH*sizeof(uint8_t));
		buf_ptr += (tree->mt->level[i]->elems)*HASH_LENGTH;
	}
}