# Backend Stack Detection Reference

## Framework Detection

Check project root in priority order. First match wins.

| Priority | Stack | Detection Command | Match Condition |
|----------|-------|-------------------|-----------------|
| 1 | Spring Boot | `grep -l 'spring-boot' pom.xml build.gradle build.gradle.kts 2>/dev/null` | Any file contains `spring-boot` |
| 2 | Django | `ls manage.py 2>/dev/null` | `manage.py` exists |
| 3 | FastAPI | `grep -l 'fastapi' pyproject.toml setup.py requirements.txt 2>/dev/null` | Any file contains `fastapi` |
| 4 | Flask | `grep -l 'flask' pyproject.toml setup.py requirements.txt 2>/dev/null` | Any file contains `flask` |
| 5 | Rails | `grep -l 'rails' Gemfile 2>/dev/null` | `Gemfile` contains `rails` |
| 6 | Laravel | `ls artisan 2>/dev/null` | `artisan` exists |
| 7 | NestJS | `grep -l '@nestjs/core' package.json 2>/dev/null` | `package.json` contains `@nestjs/core` |
| 8 | Express | `grep -l '"express"' package.json 2>/dev/null` | `package.json` contains `express` |
| 9 | Go (Gin) | `grep -l 'gin-gonic' go.mod 2>/dev/null` | `go.mod` contains `gin-gonic` |
| 10 | Go (Echo) | `grep -l 'labstack/echo' go.mod 2>/dev/null` | `go.mod` contains `labstack/echo` |
| 11 | Go (Fiber) | `grep -l 'gofiber/fiber' go.mod 2>/dev/null` | `go.mod` contains `gofiber/fiber` |
| 12 | Go (stdlib) | `ls go.mod 2>/dev/null` | `go.mod` exists (no framework match) |

Initial detection command (run first to narrow search):

```bash
ls pom.xml build.gradle build.gradle.kts go.mod pyproject.toml setup.py manage.py Gemfile package.json composer.json artisan 2>/dev/null
```

## Test Runner Detection

| Stack | Detection | Default Runner |
|-------|-----------|---------------|
| Spring Boot | `pom.xml` → JUnit (always present) | `mvn test` or `./gradlew test` |
| Django | `grep -l 'pytest' pyproject.toml setup.cfg 2>/dev/null` | `pytest` if found, else `python manage.py test` |
| FastAPI | `grep -l 'pytest' pyproject.toml setup.cfg 2>/dev/null` | `pytest` |
| Flask | `grep -l 'pytest' pyproject.toml setup.cfg 2>/dev/null` | `pytest` |
| Rails | `grep -l 'rspec' Gemfile 2>/dev/null` | `rspec` if found, else `rails test` |
| Laravel | `grep -l 'pest' composer.json 2>/dev/null` | `pest` if found, else `phpunit` |
| NestJS | `grep -E '"vitest\|jest"' package.json 2>/dev/null` | `vitest` if found, else `jest` |
| Express | `grep -E '"vitest\|jest\|mocha"' package.json 2>/dev/null` | First match: vitest > jest > mocha |
| Go (*) | Always `go test` | `go test ./...` |

## Database Detection

### From docker-compose

```bash
grep -E 'postgres|mysql|mariadb|mongo|redis|sqlite' docker-compose.yml docker-compose.yaml compose.yml compose.yaml 2>/dev/null
```

### From environment files

```bash
grep -iE 'DATABASE_URL|DB_HOST|DB_NAME|MONGO_URI|REDIS_URL' .env .env.example .env.sample .env.development 2>/dev/null
```

### From framework config

| Stack | Config Location | Detection |
|-------|----------------|-----------|
| Django | `*/settings.py` | `grep -r "DATABASES" */settings.py 2>/dev/null` |
| Rails | `config/database.yml` | `cat config/database.yml 2>/dev/null` |
| Laravel | `config/database.php` | `grep -E 'mysql\|pgsql\|sqlite' config/database.php 2>/dev/null` |
| Spring Boot | `src/main/resources/application.*` | `grep -E 'datasource\|spring.jpa' src/main/resources/application.* 2>/dev/null` |
| Express/NestJS | `package.json` | `grep -E '"pg"\|"mysql2"\|"mongoose"\|"typeorm"\|"prisma"\|"sequelize"\|"knex"\|"drizzle"' package.json 2>/dev/null` |
| Go | `go.mod` | `grep -E 'lib/pq\|go-sql-driver\|mongo-driver\|gorm\|sqlx\|ent' go.mod 2>/dev/null` |
| FastAPI/Flask | `requirements.txt`, `pyproject.toml` | `grep -iE 'sqlalchemy\|psycopg\|pymongo\|tortoise\|peewee\|prisma' requirements.txt pyproject.toml 2>/dev/null` |

### DB Access Commands

| DB Type | Docker Exec Pattern | Local CLI |
|---------|-------------------|-----------|
| PostgreSQL | `docker exec -i <container> psql -U <user> -d <db>` | `psql -U <user> -d <db>` |
| MySQL/MariaDB | `docker exec -i <container> mysql -u <user> -p<pass> <db>` | `mysql -u <user> -p<pass> <db>` |
| MongoDB | `docker exec -i <container> mongosh <db>` | `mongosh <db>` |
| SQLite | N/A | `sqlite3 <path>` |

## API Style Detection

### REST

```bash
# Framework-specific route patterns
# Rails
grep -rn 'get\|post\|put\|patch\|delete\|resources\|resource' config/routes.rb 2>/dev/null

# Django
grep -rn 'path\|re_path\|url' */urls.py 2>/dev/null

# FastAPI
grep -rn '@app\.\(get\|post\|put\|patch\|delete\)\|@router\.\(get\|post\|put\|patch\|delete\)' *.py **/*.py 2>/dev/null

# Express/NestJS
grep -rn 'router\.\(get\|post\|put\|patch\|delete\)\|@Get\|@Post\|@Put\|@Patch\|@Delete' src/ routes/ 2>/dev/null

# Spring Boot
grep -rn '@GetMapping\|@PostMapping\|@PutMapping\|@DeleteMapping\|@RequestMapping' src/ 2>/dev/null

# Laravel
grep -rn "Route::\(get\|post\|put\|patch\|delete\|resource\)" routes/ 2>/dev/null

# Go (Gin/Echo/Fiber)
grep -rn '\.GET\|\.POST\|\.PUT\|\.PATCH\|\.DELETE\|\.Handle\|\.HandleFunc' *.go **/*.go 2>/dev/null
```

### GraphQL

```bash
ls schema.graphql schema.gql **/*.graphql **/*.gql 2>/dev/null
grep -rE 'graphql|apollo-server|@nestjs/graphql|graphene|ariadne|strawberry|gqlgen' package.json pyproject.toml requirements.txt go.mod Gemfile 2>/dev/null
```

### gRPC

```bash
ls **/*.proto 2>/dev/null
grep -rE 'grpc|tonic|grpcio' package.json pyproject.toml requirements.txt go.mod Gemfile Cargo.toml 2>/dev/null
```

## Endpoint Extraction Patterns

These commands extract endpoint paths for testing. Output should be parsed into `METHOD /path` format.

| Stack | Command |
|-------|---------|
| Rails | `rails routes 2>/dev/null \|\| rake routes 2>/dev/null` |
| Django | `python manage.py show_urls 2>/dev/null` (requires django-extensions) |
| FastAPI | `grep -rn '@app\.\(get\|post\|put\|patch\|delete\)\|@router\.\(get\|post\|put\|patch\|delete\)' --include='*.py' .` |
| Express | `grep -rn "router\.\(get\|post\|put\|patch\|delete\)\|app\.\(get\|post\|put\|patch\|delete\)" --include='*.js' --include='*.ts' src/ routes/` |
| Spring Boot | `grep -rn '@\(Get\|Post\|Put\|Delete\|Patch\|Request\)Mapping' --include='*.java' --include='*.kt' src/` |
| Laravel | `php artisan route:list 2>/dev/null` |
| NestJS | `grep -rn '@\(Get\|Post\|Put\|Delete\|Patch\)' --include='*.ts' src/` |
| Go | `grep -rn '\.GET\|\.POST\|\.PUT\|\.PATCH\|\.DELETE\|HandleFunc' --include='*.go' .` |

## OpenAPI/Swagger Spec Detection

```bash
ls openapi.json openapi.yaml openapi.yml swagger.json swagger.yaml swagger.yml api-spec.json api-spec.yaml docs/openapi.* docs/swagger.* 2>/dev/null
find . -maxdepth 3 -name 'openapi.*' -o -name 'swagger.*' 2>/dev/null | head -5
```

## Migration Status Commands

| Stack | Command |
|-------|---------|
| Rails | `rails db:migrate:status` |
| Django | `python manage.py showmigrations` |
| Laravel | `php artisan migrate:status` |
| Spring Boot (Flyway) | Check `flyway_schema_history` table |
| Spring Boot (Liquibase) | Check `databasechangelog` table |
| Node (Prisma) | `npx prisma migrate status` |
| Node (TypeORM) | `npx typeorm migration:show` |
| Node (Knex) | `npx knex migrate:status` |
| Node (Drizzle) | `npx drizzle-kit status` |
| Go (golang-migrate) | `migrate -database <url> -path <dir> version` |
