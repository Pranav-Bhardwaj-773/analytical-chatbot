ALTER TABLE "auth_sessions" ADD COLUMN IF NOT EXISTS "id" TEXT;
UPDATE "auth_sessions" SET "id" = gen_random_uuid()::text WHERE "id" IS NULL;
ALTER TABLE "auth_sessions" ALTER COLUMN "id" SET NOT NULL;
DO $$ BEGIN
  ALTER TABLE "auth_sessions" ADD CONSTRAINT "auth_sessions_pkey" PRIMARY KEY ("id");
EXCEPTION
  WHEN duplicate_object THEN NULL;
END $$;
