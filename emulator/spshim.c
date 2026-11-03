// Desktop-only stand-in for the few libserialport calls cc-master uses.
// libserialport rejects pseudo-terminals (/dev/pts/N), which socat creates,
// so for emulation we open the port with plain POSIX termios instead.
// Not used on the Duo: there cc-master talks to a real UART.

#define _DEFAULT_SOURCE
#include <errno.h>
#include <fcntl.h>
#include <poll.h>
#include <stdlib.h>
#include <string.h>
#include <termios.h>
#include <time.h>
#include <unistd.h>
#include <libserialport.h>

struct sp_port { char *name; int fd; };

enum sp_return sp_get_port_by_name(const char *name, struct sp_port **out)
{
    struct sp_port *p = calloc(1, sizeof *p);
    if (!p) return SP_ERR_MEM;
    p->name = strdup(name);
    p->fd = -1;
    *out = p;
    return SP_OK;
}

enum sp_return sp_open(struct sp_port *p, enum sp_mode flags)
{
    p->fd = open(p->name, O_RDWR | O_NOCTTY);
    if (p->fd < 0) return SP_ERR_FAIL;
    struct termios t;
    if (tcgetattr(p->fd, &t) == 0) { cfmakeraw(&t); tcsetattr(p->fd, TCSANOW, &t); }
    return SP_OK;
}

enum sp_return sp_set_xon_xoff(struct sp_port *p, enum sp_xonxoff x) { return SP_OK; }
enum sp_return sp_set_baudrate(struct sp_port *p, int baud) { return SP_OK; }
char *sp_get_port_usb_manufacturer(const struct sp_port *p) { return NULL; }

enum sp_return sp_nonblocking_write(struct sp_port *p, const void *buf, size_t count)
{
    ssize_t n = write(p->fd, buf, count);
    return n < 0 ? SP_ERR_FAIL : (enum sp_return)n;
}

enum sp_return sp_blocking_read(struct sp_port *p, void *buf, size_t count, unsigned int timeout_ms)
{
    size_t got = 0;
    struct timespec t0; clock_gettime(CLOCK_MONOTONIC, &t0);
    while (got < count) {
        int wait = -1;
        if (timeout_ms) {
            struct timespec t; clock_gettime(CLOCK_MONOTONIC, &t);
            long el = (t.tv_sec - t0.tv_sec) * 1000 + (t.tv_nsec - t0.tv_nsec) / 1000000;
            wait = (int)timeout_ms - (int)el;
            if (wait <= 0) break;
        }
        struct pollfd pfd = { p->fd, POLLIN, 0 };
        int r = poll(&pfd, 1, wait);
        if (r < 0) { if (errno == EINTR) continue; return SP_ERR_FAIL; }
        if (r == 0) break;
        ssize_t n = read(p->fd, (char *)buf + got, count - got);
        if (n < 0) { if (errno == EINTR || errno == EAGAIN) continue; return SP_ERR_FAIL; }
        if (n == 0) break;
        got += (size_t)n;
    }
    return (enum sp_return)got;
}

enum sp_return sp_close(struct sp_port *p) { if (p->fd >= 0) close(p->fd); p->fd = -1; return SP_OK; }
void sp_free_port(struct sp_port *p) { if (p) { free(p->name); free(p); } }
