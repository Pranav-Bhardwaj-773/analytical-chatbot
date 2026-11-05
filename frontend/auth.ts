import { PrismaAdapter } from "@auth/prisma-adapter";
import bcrypt from "bcryptjs";
import NextAuth, { CredentialsSignin, type NextAuthConfig } from "next-auth";
import Credentials from "next-auth/providers/credentials";
import Google from "next-auth/providers/google";

import { authConfig } from "@/auth.config";
import { prisma } from "@/lib/prisma";

class EmailNotVerifiedError extends CredentialsSignin {
  code = "email_not_verified";
}

class InvalidCredentialsError extends CredentialsSignin {
  code = "invalid_credentials";
}

const googleEnabled =
  Boolean(process.env.GOOGLE_CLIENT_ID) && Boolean(process.env.GOOGLE_CLIENT_SECRET);

const providers: NextAuthConfig["providers"] = [
  Credentials({
    credentials: {
      email: { label: "Email", type: "email" },
      password: { label: "Password", type: "password" },
    },
    async authorize(credentials) {
      const email = credentials?.email?.toString().trim().toLowerCase();
      const password = credentials?.password?.toString();
      if (!email || !password) {
        throw new InvalidCredentialsError();
      }

      const user = await prisma.user.findUnique({ where: { email } });
      if (!user?.passwordHash) {
        throw new InvalidCredentialsError();
      }
      if (!user.emailVerified) {
        throw new EmailNotVerifiedError();
      }

      const valid = await bcrypt.compare(password, user.passwordHash);
      if (!valid) {
        throw new InvalidCredentialsError();
      }

      return {
        id: user.id,
        email: user.email,
        name: user.name,
        image: user.image,
      };
    },
  }),
];

if (googleEnabled) {
  providers.unshift(Google);
}

export const { handlers, signIn, signOut, auth } = NextAuth({
  ...authConfig,
  adapter: PrismaAdapter(prisma),
  providers,
  callbacks: {
    ...authConfig.callbacks,
    async signIn({ user, account, profile }) {
      if (account?.provider === "google") {
        const googleProfile = profile as { email_verified?: boolean } | undefined;
        if (googleProfile?.email_verified === false) {
          return false;
        }
        if (user.email) {
          await prisma.user.updateMany({
            where: { email: user.email.toLowerCase() },
            data: { emailVerified: new Date() },
          });
        }
        return true;
      }
      return true;
    },
  },
});
