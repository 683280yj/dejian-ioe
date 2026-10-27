# b2b — To B 交易模块（lane-c）

企业客户/经销商、采购单、批发订单、供应商对账、应收应付。复用 `inventory.Product / Supplier`，仓库用 `tenancy.Warehouse`，
入库/发货通过 `inventory.models.inventory.update_inventory` 记库存流水，操作写 `inventory.OperationLog`。

## 铁律
所有状态推进只在 `b2b/services.py`，必须传入已登录、启用的真人 `actor` 并校验权限；视图只接受 POST。
无信号、无定时任务、无 save() 钩子推进状态。AI 只可读或生成 DRAFT。系统不发起任何支付（无支付宝）。

| 单据 | 流转（人工按钮） | 权限 |
|---|---|---|
| 采购单 | DRAFT→SUBMITTED→APPROVED→RECEIVED（入库+生成应付）；前三态可 CANCELLED | approve/receive_purchaseorder |
| 批发订单 | DRAFT→SUBMITTED→APPROVED→SHIPPED（出库+生成应收）→COMPLETED；发货前可 CANCELLED | approve/ship_wholesaleorder |
| 应付/应收 | OPEN→PARTIAL→SETTLED（登记线下付/收款） | record_payment / record_receipt |
| 对账单 | DRAFT→CONFIRMED（差异须为 0）/DISPUTED | confirm_supplierstatement |

## 依赖 / 注册
- tenant 外键：`models.ForeignKey('tenancy.Tenant', null=True, blank=True, on_delete=models.PROTECT)`；
  迁移依赖 `('tenancy', '__first__')`。正式环境需 lane-a 的 `tenancy` app。
- 租户过滤读 `request.tenant`（lane-a 中间件）；为空时不过滤。
- 测试：`.venv/bin/python manage.py test b2b --settings=b2b.test_settings`
  （lane-a 合并后 tenancy 为正式 app，`_tenancy_stub` 已移除；也可直接用 `--settings=inventory.test_settings`）。
