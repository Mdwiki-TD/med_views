from src.services.mw_views import PageviewsClient

view_bot = PageviewsClient()
data = view_bot.article_views_new('ar.wikipedia', ["الصفحة الرئيسة"], granularity='monthly', start='20100101', end='20250627')
# ---
for title, views in data.items():
    print(title)
    print(views)
