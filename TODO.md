# 🌚 TODO - Miss Valentina

___

### ⚡ Top Priority

- [ ] cleanup `main.py` (move gpt stuff to a utils/gpt.py file)
- [ ] instead of `femdom.py` & `femdom2.py` (ambiguous), use `sub.py` & `dom.py` files.
- [ ] global error handler, dont run commands if the bot doesnt have necessary permissions.
- 

### ✈️ Medium Priority

- [ ] asyncronous & better database usage 
  - add the asyncpg pool connection to a custom context and use it in the commands.
  - sample use:
  - ```python
    # utils/database.py
    class DatabaseFunctions:
      def __init__(self, pool: asyncpg.pool.Pool):
        self.pool = pool
      
      async def add_user(self, user: discord.User):
        await self.pool.execute("INSERT INTO users (id) VALUES ($1)", user.id)
    
    # a command
    async def a_command(ctx: Ctx):
      await ctx.db.add_user(ctx.author)
    ```