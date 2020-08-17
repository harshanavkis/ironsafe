#ifndef PERF_COUNTER_H
#define PERF_COUNTER_H

#include <sys/time.h>

struct timeval start_codec, end_codec;
struct timeval kdf_start, kdf_end;
struct timeval mt_start, mt_end;
double total_enc_time;
double total_kdf_time;
double mt_verify_time;
unsigned int num_codec_enc, num_codec_dec;

#endif /* PERF_COUNTER_H */