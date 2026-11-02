export interface Book {
  id: number
  title: string
  author: string
  category: string
  description: string
  price: number
  total_copies: number
  available_copies: number
  cover_image: string
  created_at: number
}

export type NavbarUser = {
  name?: string | null;
  email?: string | null;
  image?: string | null;
};

export type NavbarProps = {
  isAuthenticated: boolean;
  user: NavbarUser | null;
  onLogout: () => void | Promise<void>;
};
