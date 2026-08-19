-- 修复 fund_related / fund_secid 的 RLS：允许匿名读取（公共静态数据）
-- 在 Supabase SQL Editor 或 psql 中执行

ALTER TABLE public.fund_related DISABLE ROW LEVEL SECURITY;
ALTER TABLE public.fund_secid  DISABLE ROW LEVEL SECURITY;

-- 或（更推荐，保留 RLS 但允许 anon 读）：
-- DROP POLICY IF EXISTS "Allow public select fund_related" ON public.fund_related;
-- CREATE POLICY "Allow public select fund_related" ON public.fund_related
--   FOR SELECT USING (true);
-- DROP POLICY IF EXISTS "Allow public select fund_secid" ON public.fund_secid;
-- CREATE POLICY "Allow public select fund_secid" ON public.fund_secid
--   FOR SELECT USING (true);

-- 注意：这两张表是公开的基金->板块静态映射，无敏感数据，可安全放开 anon 读取
