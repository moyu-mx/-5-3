/* Mock Linux kernel: kernel/sched/fair.c (excerpt) */
#include <linux/sched.h>

static void enqueue_task_fair(struct rq *rq, struct task_struct *p)
{
	struct cfs_rq *cfs_rq;
	struct sched_entity *se = &p->se;

	cfs_rq = kzalloc(sizeof(*cfs_rq), GFP_KERNEL);
	cfs_rq->nr_running = 1;
	se->cfs_rq = cfs_rq;
}

static int fair_proc_init(struct proc_dir_entry *parent)
{
	struct fair_data *fd;

	fd = devm_kzalloc(parent->dev, sizeof(*fd), GFP_KERNEL);
	if (!fd)
		return -ENOMEM;
	parent->data = fd;
	return 0;
}
