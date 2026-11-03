// Portable counting semaphore for building cc-master on macOS.
// macOS doesn't implement unnamed POSIX semaphores (sem_init fails, no
// sem_timedwait). This replaces them with a mutex + condition variable.
// Force-included by the Makefile on every platform, so the Linux build tests
// the same code that runs on the Mac.
#ifndef PORTSEM_H
#define PORTSEM_H

#include <errno.h>
#include <pthread.h>
#include <semaphore.h>   // pull in the system one first, then override names
#include <time.h>

typedef struct { pthread_mutex_t m; pthread_cond_t c; unsigned v; } portsem_t;

static inline int portsem_init(portsem_t *s, int pshared, unsigned v)
{
    (void)pshared;
    pthread_mutex_init(&s->m, NULL);
    pthread_cond_init(&s->c, NULL);   // default clock = CLOCK_REALTIME, as sem_timedwait
    s->v = v;
    return 0;
}

static inline int portsem_post(portsem_t *s)
{
    pthread_mutex_lock(&s->m);
    s->v++;
    pthread_cond_signal(&s->c);
    pthread_mutex_unlock(&s->m);
    return 0;
}

static inline int portsem_wait(portsem_t *s)
{
    pthread_mutex_lock(&s->m);
    while (s->v == 0) pthread_cond_wait(&s->c, &s->m);
    s->v--;
    pthread_mutex_unlock(&s->m);
    return 0;
}

static inline int portsem_timedwait(portsem_t *s, const struct timespec *abs)
{
    int r = 0;
    pthread_mutex_lock(&s->m);
    while (s->v == 0 && r == 0) r = pthread_cond_timedwait(&s->c, &s->m, abs);
    if (s->v > 0) { s->v--; r = 0; }
    pthread_mutex_unlock(&s->m);
    if (r) { errno = r; return -1; }
    return 0;
}

#define sem_t          portsem_t
#define sem_init       portsem_init
#define sem_post       portsem_post
#define sem_wait       portsem_wait
#define sem_timedwait  portsem_timedwait

#endif
