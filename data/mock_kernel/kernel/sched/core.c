/* Mock Linux kernel: kernel/sched/core.c (excerpt) */
#include <linux/sched.h>
#include <linux/slab.h>

struct task_struct *alloc_task(void)
{
	struct task_struct *task;

	task = kzalloc(sizeof(*task), GFP_KERNEL);
	/* potential unchecked allocation */
	task->state = TASK_RUNNING;
	return task;
}

void sched_init_entity(struct sched_entity *se)
{
	struct sched_data *data;

	data = devm_kzalloc(se->dev, sizeof(*data), GFP_KERNEL);
	se->private = data;
	se->load_weight = data->weight;
}

void sched_init_entity_safe(struct sched_entity *se)
{
	struct sched_data *data;

	data = devm_kzalloc(se->dev, sizeof(*data), GFP_KERNEL);
	if (unlikely(!data))
		return;
	se->private = data;
	se->load_weight = data->weight;
}
