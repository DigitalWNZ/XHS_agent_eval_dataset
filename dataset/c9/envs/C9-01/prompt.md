我经营一家潮玩零售店，希望制作一个集商品销售、订单管理和售后处理于一体的网站。最终交付一个自包含的 HTML 文件，双击即可使用，无需后端或联网加载资源。所有付款和退款均为本地模拟，不接真实支付。
请自行构造一组商品和历史订单。商品应包含不同规格、价格和库存；历史订单应覆盖待付款、已付款、已发货、已取消以及发生过部分退款等情况。
网站需要支持以下完整业务流程：
1. 商品与购物车：搜索、筛选商品，选择规格加入购物车，修改数量、移除商品。实时计算金额，并阻止无库存、超库存和非法数量的操作。
2. 优惠计算：支持满减券和会员折扣，明确展示适用条件、叠加规则及优惠明细。改变商品、数量或会员身份后，重新计算优惠；不能保留已经失效的优惠金额。
3. 结算与订单生成：填写并校验收货信息，确认金额后生成可查询的订单。下单时占用库存；重复点击确认不能创建重复订单，也不能重复扣库存。
4. 订单状态流转：可以模拟付款、发货、取消订单等操作。不同状态允许的操作应不同。未发货订单取消后释放库存，重复取消不能再次增加库存。
5. 部分退款与退货：可以选择订单中的部分商品和数量申请售后。退款金额需要考虑原订单实际支付及优惠分摊，不能按原价直接退款；累计退款不能超过实付金额，售后数量不能超过可退数量。
6. 库存与售后联动：已发货商品不能仅因退款申请就增加库存；只有确认退货入库后才回补，且不能重复入库。展示各项操作的记录。
7. 查询与统计：按订单号、商品、状态和时间筛选订单。销售额、退款额、净收入及商品销量，应由实际记录计算，并随操作更新，不能使用固定展示数字。
8. 保存与备份：刷新后恢复数据；支持导出完整业务数据并重新导入。错误或不完整的导入文件应给出提示，不能覆盖已有有效数据。
请做成适合店员日常使用的工作台，提供清晰的金额明细、状态提示和危险操作确认。交付前自行测试“下单→付款→发货→部分退货退款→确认入库”以及“下单→取消”的流程，最终提供 HTML 文件，并说明操作方式和已知限制。

---
【交付与验收约定（评测补充说明）】
- 交付文件：/app/index.html（单个文件，内联全部 CSS/JS；不得引用任何外部网络资源，也不要拆分出其他文件）。验收时用 Chromium 以 file:// 打开，网络被禁止。
- 页面加载后须在 window.shopTestAPI 上提供以下方法，供自动化验收调用。它们必须调用与界面相同的业务逻辑（不能是单独的模拟实现），全部为同步方法，返回可 JSON 序列化的普通对象。金额一律以“元”为单位、保留两位小数的数字。操作类方法返回 { ok: true, ... } 或 { ok: false, error: "原因" }；失败时不得改变任何数据。
  - reset()：恢复为你构造的初始商品与历史订单（清空购物车，会员身份设为否）。
  - getState() → { products: [{ id, name, variants: [{ sku, spec, price, stock }] }], coupons: [{ code, threshold, amount }]（满 threshold 元减 amount 元）, isMember, orders: [订单], logs: [{ time, action, detail }] }
    订单 = { id, status, createdAt（ISO 时间字符串）, paidAt（从未付款为 null）, items: [{ sku, qty, unitPrice }], subtotal（商品原价合计）, discounts: [{ type: "member" | "coupon", amount }], payable（实付）, refundedAmount（累计退款）, refunds: [{ id, items: [{ sku, qty }], amount, returnGoods, restocked }] }
    status 只能是 "pending"（待付款）、"paid"（已付款）、"shipped"（已发货）、"cancelled"（已取消）之一；部分退款不改变 status，通过 refunds / refundedAmount 体现。
  - setMember(true|false)；addToCart(sku, qty)；setCartQty(sku, qty)；removeFromCart(sku)；applyCoupon(code 或 null)
  - getCart() → { lines: [{ sku, qty, unitPrice, lineTotal }], subtotal, discounts: [{ type, amount }], total }，其中 total = subtotal − 各项优惠之和。会员折扣为固定比例，对任意非空购物车生效。
  - checkout(address) → { ok, orderId }：address = { name, phone, address }（phone 为 11 位手机号）；校验失败返回 ok:false。成功后清空购物车。
  - prepareCheckout(address)：以当前购物车进入界面上的“确认金额”步骤，此时页面上可见一个带 data-testid="confirm-order" 属性的“确认下单”按钮（点击它即下单；可以带确认弹窗）。
  - pay(orderId)；ship(orderId)；cancel(orderId)：允许取消待付款和已付款未发货的订单；取消已付款订单时自动产生一条退还剩余实付的退款记录。
  - requestAfterSale(orderId, [{ sku, qty }], { returnGoods: true|false }) → { ok, refundId, amount }：已付款或已发货订单可申请；退款在申请时即记入。退款金额按比例分摊优惠：本次退款 = Σ 数量 × 单价 × 实付 ÷ 商品原价合计，四舍五入到分；当订单商品全部退完时，最后一次退款为剩余实付。
  - confirmReturn(refundId)：已发货订单的退货确认入库，回补库存；同一售后单只能入库一次。
  - queryOrders({ orderId?, sku?, status?, from?, to? }) → [订单]：from / to 为 "YYYY-MM-DD"（含当天）。
  - getStats() → { sales, refunds, net, unitsSold: { sku: 数量 } }：sales = 所有曾付款订单（paidAt 非空，含之后取消或退款的）实付合计；refunds = 全部退款记录合计；net = sales − refunds；unitsSold = 曾付款订单中各 SKU 数量 − 已退数量。
  - exportData() → 字符串（JSON，其中商品列表字段名为 products、订单列表字段名为 orders）；importData(字符串) → { ok, error }。
- 数据保存在浏览器本地存储中，刷新页面后保持。
- 环境提示：工作目录为 /app（初始为空）。容器内已预装 Chromium（PLAYWRIGHT_BROWSERS_PATH=/ms-playwright），可用 `uvx -p 3.12 --with playwright==1.55.0 python 你的脚本.py` 编写并运行浏览器自测脚本（自测脚本不要放进最终交付）。
