"""Case texts for the XHS evaluation sheet (C6 hill climb / C7 daily job, 2026-10-15 layout)."""

DESC = {
 "C6-01": "编写 Python 脚本 /app/filter.py，原地清除 HTML 文件中的所有 JavaScript（script 标签、on* 事件属性、javascript: 链接等）以防 XSS，同时尽量保留原有 HTML 结构和格式不变。考察安全过滤的完整性与“不误伤正常内容”的平衡。",
 "C6-02": "在 Go 嵌入式 KV 存储 Pebble 中新增“写入持久化完成”能力：新增 BatchDurable 事件回调（Sync 提交后 WAL 落盘时触发一次），以及按序列号 / 任务 ID 等待持久化的一组 DB 方法（含 context 版本、过期任务报错、统计指标）。考察在大型存储引擎中做并发安全的功能扩展。",
 "C6-03": "编写 OpenCV 脚本 jump_analyzer.py，分析跨栏运动员的 MP4 视频，自动检测起跳帧和落地帧，并按指定字段输出 TOML 文件。只能使用 cv2 / numpy / toml。考察计算机视觉算法设计与鲁棒性。",
 "C6-04": "使用指定版本的 bge-small-zh-v1.5 中文向量模型，对 /app/data.txt 中每行文档计算与查询“terminal-bench”的余弦相似度，找出第 5 高的文档写入 result.txt。考察按要求精确使用嵌入模型和检索工具。",
 "C6-05": "编写一个 C 与 Python 的“多语言共存”单文件 main.py.c：既能用 python3 直接运行，也能用 gcc 编译后运行，两种方式都输出第 N 个斐波那契数。还隐含要求不在目录里留下多余文件（如编译产物）。",
 "C6-06": "实现异步函数 run_tasks(tasks, max_concurrent)：限制最大并发数运行一批异步任务，并保证用户按 Ctrl-C 中断时各任务的清理代码仍能执行。考察 asyncio 并发控制与取消 / 中断语义。",
 "C6-07": "在 TanStack Query（TypeScript）中修复“细粒度持久化查询”的恢复逻辑：从存储恢复的查询要完整保留缓存状态（过期标记、错误、失败次数、时间戳、无限分页参数），新增导出 createPersisterRestoreResult 辅助函数，并保证单条恢复与批量恢复行为一致、在各框架适配层可见。",
 "C7-01": "为 TypeScript ORM 框架 drizzle-orm 新增类型安全的 SQL 窗口函数构建器：rowNumber / rank / lag / lead / windowSum 等及 .over() 规格（partitionBy、orderBy、rows/range 帧），并对非法参数给出明确报错，跨方言生成正确 SQL。",
 "C7-02": "修复一个 WAL 模式下 WAL 文件被损坏 / 加密的 SQLite 数据库，使其能读出全部 11 条记录（而非仅基础表中的 5 条），并按 id 排序导出为 recovered.json。考察数据恢复与二进制格式分析能力。",
 "C7-03": "修复 Django 的一个 ORM bug：使用 only() 延迟加载字段并通过嵌套 Prefetch 回到“父”对象时，延迟字段集合判断错误，导致访问已预取的字段仍触发额外数据库查询。",
 "C7-04": "修复 Django 3.1 的性能回归：Model.objects.all().delete() 生成了带子查询的 DELETE 语句（DELETE … WHERE id IN (SELECT …)），导致 MySQL 下 LOCK TABLES 失败且大表删除很慢；需恢复为简单的 DELETE FROM。",
 "C7-05": "修复 Django JSONField 的 has_key / has_keys / has_any_keys 查询：在 SQLite、MySQL、Oracle 上无法匹配数字形式的键（如 '1111'），需让数字键与字符串键一样被正确查询。",
 "C7-06": "修复 Django MySQL 后端仍使用 mysqlclient 已废弃的连接参数 db / passwd 的问题，改为新参数 database / password，并保持兼容。",
 "C7-07": "修复 Django 发送邮件时的崩溃：当主机名包含非 ASCII 字符（如“正宗”）且邮件编码为非 Unicode（如 iso-8859-1）时，Message-ID 等头部编码失败；需在生成头部前把域名转换为 punycode。",
 "C7-08": "修复 Python requests 库在 Python 3.8.12 下使用带认证的代理时返回 407 的问题（因标准库 URL 解析行为变化导致代理认证信息丢失），确保代理认证头被正确发送。",
 "C7-09": "为 Kubernetes 网关 kgateway 的 TrafficPolicy 新增 consistentHash 一致性哈希配置（按 header、cookie、查询参数、filterState、源 IP 计算哈希），完成 CRD 校验规则，并正确转换为 Envoy RouteAction 的 hash_policy。",
 "C7-10": "为 Go 数据库备份工具 onedump 新增备份加密模块：基于 AES-256-GCM 的分块流式加密 / 解密（固定头部格式、每块唯一 nonce、结尾 HMAC 完整性校验），并对错误密钥、篡改数据、版本不符给出明确错误，接入备份流程。",
 "C7-11": "为 Go 地理空间库 geo 的 ShapeIndex 实现二进制序列化 Encode / Decode：所有内置 Shape 类型可往返、Shape ID 与空间单元结构完整保留（解码后无需重建即可查询），且对截断、损坏、超大分配等恶意输入返回错误而不是 panic。",
}

# Short prompts are kept verbatim (filled from the dataset); long prompts are summarised here.
INPUT_SUMMARY = {
 "C6-02": "(Summary of the original prompt) Pebble (Go KV store): add EventListener.BatchDurable(BatchDurableInfo) that fires exactly once per Sync commit after the WAL sync completes, even on failure (fields: JobID, SeqNum, Err, ApplyDuration, SyncDuration, CorrelationID from WriteOptions.CommitCorrelationID, BatchSize, KeyCount); never for non-sync commits or DisableWAL. Add DB methods on every DB: WaitForDurability / WaitForDurabilityBatch / WaitForJobDurability (+ Context variants; durability/close errors win over context cancellation; jobs outside a bounded retention window return an 'expired' error), plus durability state/notification/stats methods and metrics. Keep the commit path and public types backward compatible.",
 "C6-07": "(Summary of the original prompt) TanStack Query: fine-grained persisted queries must restore the full observable query state, not look like a fresh successful fetch. Restored entries keep data together with stale markers, refetch errors, failure counters, timestamps and infinite-query page params, both when restored one at a time during query execution and when the cache is rebuilt in bulk from storage. Add a public helper createPersisterRestoreResult({ data, state }) exported from query-core; when a persister returns it, the query is treated as a restored snapshot. The behaviour must be visible through the public results of the supported framework adapters.",
 "C7-01": "(Summary of the original prompt) drizzle-orm: add type-safe window-function builders. Ranking: rowNumber, rank, denseRank, ntile, percentRank, cumeDist; offset: lag, lead, firstValue, lastValue, nthValue; aggregates: windowSum, windowAvg, windowMin, windowMax, windowCount. Each returns a builder with .over(spec | windowName); spec has partitionBy, orderBy, frame built with rows()/range() and boundaries unboundedPreceding, currentRow, unboundedFollowing, preceding(n), following(n). Constraints: numeric positional args are never bound parameters; ntile/nthValue reject non-positive integers (message names the function and value); .window() rejects empty / whitespace names; frames reject from-after-to; correct SQL per dialect.",
 "C7-03": "(Summary of the original prompt) Repo django/django at /testbed. Fix the issue without modifying existing tests (hidden tests decide): with User.objects.only('email').prefetch_related(Prefetch('profile', queryset=Profile.objects.prefetch_related(Prefetch('user', queryset=User.objects.only('kind'))))), accessing user.profile.user.kind triggers an extra query because the inner User instance wrongly inherits the outer instance's deferred fields. Expected: 3 queries for the fetch and 0 queries for user.profile.user.kind.",
 "C7-04": "(Summary of the original prompt) Repo django/django at /testbed. Fix the issue without modifying existing tests: Model.objects.all().delete() on Django 3.1 generates 'DELETE FROM t WHERE t.id IN (SELECT t.id FROM t)' instead of 'DELETE FROM t'. The subquery breaks MySQL LOCK TABLES (a locked table can't be referenced twice without aliases) and is much slower on large tables. Restore the simple DELETE when no filtering/joins require a subquery.",
 "C7-05": "(Summary of the original prompt) Repo django/django at /testbed. Fix the issue without modifying existing tests: JSONField lookups has_key, has_keys and has_any_keys don't find numeric keys (e.g. {'1111': 'bar'} with has_key='1111') on SQLite, MySQL and Oracle (PostgreSQL works). Make numeric-looking keys be treated as object keys in these lookups.",
 "C7-07": "(Summary of the original prompt) Repo django/django at /testbed. Fix the issue without modifying existing tests: when the machine hostname is non-ASCII (e.g. '正宗') and EMAIL encoding is non-unicode (iso-8859-1), building an email crashes with UnicodeEncodeError because the Message-ID header (from DNS_NAME) can't be encoded. Django should convert the domain name to punycode before using it in headers.",
 "C7-08": "(Summary of the original prompt) Repo psf/requests at /testbed (requests 2.27.0, urllib3 1.26.7). Fix the issue without modifying existing tests (hidden tests decide): 'Proxy authentication bug' - with Python 3.8.12, requests.get('https://example.org/', proxies=proxies) through an authenticated proxy returns 407 instead of 200, while other Python versions work; the reporter suspects the notable changes in Python 3.8.12.",
 "C7-09": "(Summary of the original prompt) kgateway: add spec.consistentHash to TrafficPolicy with sub-fields disable (when true no other fields allowed), headers (headerName, optional regexRewrite pattern/substitution, terminal), cookies (name, ttl, path, attributes, terminal), queryParameters, filterState and sourceIp (each with terminal). Runtime: when consistentHash is set (even {}), RouteAction gets hash_policy entries (default: one non-terminal sourceIp policy); disable suppresses them; entries in canonical order headers, cookies, queryParameters, filterState, sourceIp; array entries de-duplicated by key (headers case-insensitive); regexRewrite applied before hashing; cookie ttl accepts Go durations or seconds; when several TrafficPolicies target a route, arrays are unioned (higher priority first) and merge metadata records consistentHash. Work in a new branch and commit.",
 "C7-10": "(Summary of the original prompt) onedump (Go): create package encryption. NewEncryptor(key) rejects non-32-byte keys (wraps ErrInvalidKey). EncryptWriter(w) = AES-256-GCM streaming in chunks up to 64 KB: 3-byte header 0x4F 0x44 + version 0x01; each chunk = 4-byte big-endian length, 12-byte unique nonce, ciphertext + 16-byte tag; a 4-zero-byte sentinel, then a 32-byte HMAC-SHA256 over everything between header and sentinel. Close is idempotent; two encryptions of the same data differ. DecryptReader(r, key) reverses it lazily, with errors containing 'invalid header', 'unsupported version', 'integrity'; wrong keys and truncated data fail. Add encryption.Config (Enabled, KeySource env/file/literal/derive, ...) with Validate() ('mutually exclusive' sources) and LoadKey(); add config.Job.Encryption + Encrypted(), export Job.Validate(); filenames get .enc after .gz; integrate into the handler's storage pipeline with fail-fast key loading so output round-trips via DecryptReader + gzip. Work in a new branch and commit.",
}

# Short rubrics for the sheet (满分 = perfect 1.0；合格 = accept 0.6；不合格 = bad 0)
COMMON_SHORT = {
 "READABILITY": "满分：命名清晰、结构一目了然、必要处有注释。\n合格：整体可读，个别命名或注释欠佳。\n不合格：命名混乱、难以理解（如大量单字母变量、魔法逻辑无说明）。",
 "MAINTAINABILITY": "满分：职责分离清楚、无重复代码、函数短小。\n合格：结构基本合理，有少量重复、过长函数或残留调试代码。\n不合格：巨型函数（>80 行）、深层嵌套、大量复制粘贴或强耦合。上限：单函数 >100 行即不合格。",
 "ROBUSTNESS": "满分：异常处理具体、资源安全、边界输入有校验、无魔法常量。\n合格：有错误处理，但存在笼统 catch-all 或个别边界未校验。\n不合格：吞掉错误、资源泄漏风险、无输入校验或硬编码密钥。",
}
CASE_SHORT = {
 "C6-01-CASE1": "满分：用通用规则（属性名 / URL 协议规范化、标签白名单等）消除各类混淆 XSS 向量（大小写、编码、空白绕过）。\n合格：常见变体能处理，个别混淆方式漏掉。\n不合格：只按字面匹配，混淆写法即可绕过。",
 "C6-01-CASE2": "满分：只删除危险元素 / 属性 / 链接，其余标记的引号、属性顺序、空白和正常属性保持原样。\n合格：基本保留，少量无害改动。\n不合格：重新序列化导致格式大幅变化或误删正常内容。",
 "C6-02-CASE1": "满分：只新增字段和方法；非同步提交路径与原来一致；未配置回调时几乎无额外开销。\n合格：兼容，但非同步路径有少量额外开销。\n不合格：改变既有公共类型或行为，或给所有提交增加明显开销。",
 "C6-03-CASE1": "满分：校验参数和视频能否打开，无法读取或检测不到起跳时给出清晰报错并以非零码退出；阈值自适应。\n合格：有基本校验，但报错或阈值处理较粗糙。\n不合格：异常输入直接崩溃或输出错误结果。",
 "C6-03-CASE2": "满分：读取 argv[1]，在 /app/output.toml 中只输出两个规定名称的整数字段，帧号约定一致。\n合格：格式正确但有小偏差（如多余字段）。\n不合格：字段名或文件位置不符合要求。",
 "C6-04-CASE1": "满分：固定指定的模型版本，通过 mteb 正确区分查询 / 文档编码，按余弦相似度排序并正确取第 5 名（处理并列、去重）。\n合格：结果正确但排序细节处理不严谨。\n不合格：模型版本或排序方式错误。",
 "C6-05-CASE1": "满分：两种语言都满足 f(0)=0、f(1)=1；C 端用 64 位无符号迭代，至少到 n=93 仍正确；Python 端迭代实现。\n合格：常规输入正确，大数或边界有小问题。\n不合格：边界错误或大数溢出。",
 "C6-05-CASE2": "满分：严格按题目给出的两条命令即可运行（不需额外编译参数或环境变量），只输出数字，不留多余文件。\n合格：能运行但有多余输出等小问题。\n不合格：需要额外参数才能运行或留下编译产物。",
 "C6-06-CASE1": "满分：空任务列表立即返回；max_concurrent<1 报错；某任务出错时妥善取消其余任务并执行清理。\n合格：主要情况处理，个别退化参数未覆盖。\n不合格：异常时挂起、泄漏任务或跳过清理。",
 "C6-06-CASE2": "满分：签名和类型标注与要求一致，每个任务只调用一次且仅在有空位时启动，可用 from run import run_tasks 导入。\n合格：基本符合，有小偏差。\n不合格：签名不符或导入失败。",
 "C6-07-CASE1": "满分：导出的辅助函数使用不可伪造的标记；单条恢复与批量恢复共用同一套应用逻辑；恢复时不触发成功回调。\n合格：功能正确但实现有重复或标记较弱。\n不合格：两条恢复路径行为不一致或触发了错误回调。",
 "C6-07-CASE2": "满分：普通数据路径不变，新导出均为新增，createPersister 选项不变。\n合格：基本兼容，有小的接口调整。\n不合格：破坏既有 persister 用法。",
 "C7-01-CASE1": "满分：纯新增 API；各方言（pg / mysql / sqlite 等）的 .window() 行为一致；不改动现有接口。\n合格：基本兼容，个别方言不一致。\n不合格：破坏既有接口或某方言缺失。",
 "C7-02-CASE1": "满分：依据证据定位损坏原因（如比对 WAL 头部魔数推导出 XOR 密钥），完整解密后交给 SQLite 正常读取。\n合格：恢复成功但方法有试凑成分。\n不合格：手工拼凑数据或硬编码结果。",
 "C7-02-CASE2": "满分：在原地修改或用 SQLite 打开（可能触发 checkpoint）之前，先备份原始 WAL（最好连同主库）。\n合格：有备份但时机偏晚。\n不合格：未做任何备份就修改原文件。",
 "C7-03-CASE1": "满分：仅在子对象已缓存时跳过回填；未缓存时仍回填反向关系；同时处理一对一关系。\n合格：修复主场景，一对一情形未覆盖。\n不合格：无条件跳过回填，引入新问题。",
 "C7-04-CASE1": "满分：在根因处修复（统计表别名前先注册基础别名），仅真正单表删除时去掉子查询；带关联 / 过滤的删除仍正确；不为特定数据库打补丁。\n合格：修复有效但位置不在根因。\n不合格：针对 MySQL 特判或破坏关联删除。",
 "C7-05-CASE1": "满分：has_key 类查询的最后一级键在 SQLite / MySQL / Oracle 上一律按对象键处理；内部 isnull / exact=None 调用仍把整数当数组下标。\n合格：主场景修复，内部调用有小影响。\n不合格：破坏数组下标语义。",
 "C7-06-CASE1": "满分：连接参数改名为 database / password，其余参数构建逻辑不变。\n合格：改名正确，附带少量无关改动。\n不合格：仍使用旧名或改错。",
 "C7-06-CASE2": "满分：OPTIONS 中旧键名仍可作为兼容写法；不提高版本要求。\n合格：兼容但未说明。\n不合格：旧配置失效。",
 "C7-07-CASE1": "满分：在源头统一把域名转为 punycode，与邮件编码无关；ASCII 主机名不受影响；不用 try/except 掩盖问题。\n合格：修复有效，但转换位置分散。\n不合格：只针对特定编码修补或吞掉异常。",
 "C7-08-CASE1": "满分：prepend_scheme_if_needed 签名不变，只把认证信息重新拼回 netloc；不针对 urllib3 / Python 版本特判。\n合格：修复有效但改动范围偏大。\n不合格：按版本特判或改变函数其他行为。",
 "C7-09-CASE1": "满分：在 MergeTrafficPolicies 中注册专门的合并函数，实现全部合并规则（并集、去重、优先级、规范顺序），复用现有合并元数据工具。\n合格：主要规则实现，个别细节缺失。\n不合格：未实现多策略合并或语义错误。",
 "C7-09-CASE2": "满分：空配置默认源 IP 哈希、disable 抑制哈希、disable 与其他字段互斥（通过 CRD 校验体现在生成的 YAML 中）三项全部实现。\n合格：实现两项。\n不合格：仅实现一项或以下。",
 "C7-10-CASE1": "满分：只做题目要求的签名修改，所有调用方同步更新；未开启加密的任务输出和文件名与原来完全一致。\n合格：基本符合，有少量额外改动。\n不合格：未加密任务行为改变或调用方遗漏。",
 "C7-11-CASE1": "满分：只新增方法；既有编码格式逐字节不变；新增类型标签追加在末尾、不重新编号。\n合格：兼容，但有小的格式调整。\n不合格：破坏既有编码格式或 Shape 接口。",
}

# ---- C9 (customer-provided) ----
DESC["C9-01"] = "客户提供需求：为潮玩零售店制作一个自包含的单文件 HTML 网站（双击即可使用、无后端、不联网），集商品销售、订单管理和售后处理于一体：商品搜索筛选与购物车、满减券与会员折扣、下单与库存预占、模拟付款 / 发货 / 取消、按优惠分摊的部分退款与退货入库、统计与查询、本地持久化以及数据导入导出。"
INPUT_SUMMARY["C9-01"] = ("(Summary of the original prompt) 潮玩零售店需要一个自包含 HTML 文件（/app/index.html，双击可用，无后端、不联网加载资源，付款退款均为本地模拟）。"
    "自行构造商品（不同规格、价格、库存）和历史订单（覆盖待付款、已付款、已发货、已取消、部分退款）。业务流程："
    "1) 商品搜索筛选、选规格加购、改数量、移除，实时算金额，阻止无库存 / 超库存 / 非法数量；"
    "2) 满减券 + 会员折扣，展示适用条件、叠加规则和优惠明细，商品 / 数量 / 会员变化后重算，不保留失效优惠；"
    "3) 填写并校验收货信息后下单，预占库存，防止重复点击生成多单；"
    "4) 订单状态流转（模拟付款、发货、取消），取消释放库存且只释放一次；"
    "5) 部分退款与退货：按实付及优惠分摊计算退款，累计不超过实付，数量不超过可退数量，退货确认入库后才回补库存且只回补一次；"
    "6) 统计与查询基于记录实时计算；7) 刷新后数据不丢失，支持导出 / 导入，非法或截断数据拒绝导入且不覆盖现有数据；危险操作需确认。"
    "交付约定：页面需暴露 window.shopTestAPI（getState、addToCart、getCart、setMember、checkout、pay、requestAfterSale、confirmReturn、queryOrders 等）供隐藏 Playwright 测试调用。")
CASE_SHORT["C9-01-CASE1"] = "满分：金额明细完整（原价、各项优惠及适用规则 / 叠加方式、实付、退款）；订单状态清楚且只显示允许的操作；取消、退款、入库、导入、重置等危险操作均需确认；错误提示通俗易懂。\n合格：大部分具备，个别方面薄弱（如未说明叠加规则、某个危险操作无确认、报错过于简略）。\n不合格：无金额明细、状态或可用操作不清楚，或多个危险操作无确认直接执行。"
CASE_SHORT["C9-01-CASE2"] = "满分：业务逻辑只有一套，界面与测试接口共用；金额按分（整数）或精确计算；统计每次从记录推导；导入先完整校验再替换数据。\n合格：基本共用，但有少量重复（如界面单独再算一遍合计），或用浮点数但有谨慎的舍入。\n不合格：测试接口是另一套或简化实现、金额用未舍入的浮点数、统计数据写死或单独存储，或导入时先改数据再校验。"
