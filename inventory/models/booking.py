from django.db import models


class BookingLead(models.Model):
    STATUS_CHOICES = (
        ('new', '待联系'),
        ('contacted', '已联系'),
        ('closed', '已完成'),
    )

    phone = models.CharField('联系电话', max_length=20)
    category = models.CharField('经营品类', max_length=80)
    status = models.CharField('处理状态', max_length=12, choices=STATUS_CHOICES, default='new')
    created_at = models.DateTimeField('提交时间', auto_now_add=True, db_index=True)

    class Meta:
        verbose_name = '官网预约'
        verbose_name_plural = '官网预约'
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.phone} · {self.category}'
