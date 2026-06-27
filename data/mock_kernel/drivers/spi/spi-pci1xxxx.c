/* Mock Linux kernel: drivers/spi/spi-pci1xxxx.c (excerpt) */
#include <linux/kernel.h>
#include <linux/spi/spi.h>

static int pci1xxxx_spi_probe(struct pci_dev *pdev)
{
	struct spi_bus *spi_bus;
	int iter;

	spi_bus->spi_int[iter] = devm_kzalloc(&pdev->dev,
		sizeof(*spi_bus->spi_int[iter]), GFP_KERNEL);
	/* BUG: missing null check here in buggy version */
	spi_sub_ptr = spi_bus->spi_int[iter];
	spi_sub_ptr->spi_host = devm_spi_alloc_host(&pdev->dev,
		sizeof(struct spi_host));
	return 0;
}

static int pci1xxxx_spi_probe_fixed(struct pci_dev *pdev)
{
	struct spi_bus *spi_bus;
	int iter;

	spi_bus->spi_int[iter] = devm_kzalloc(&pdev->dev,
		sizeof(*spi_bus->spi_int[iter]), GFP_KERNEL);
	if (!spi_bus->spi_int[iter])
		return -ENOMEM;
	spi_sub_ptr = spi_bus->spi_int[iter];
	return 0;
}
