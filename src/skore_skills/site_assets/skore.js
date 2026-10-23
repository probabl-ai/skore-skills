(() => {
  const script = document.querySelector('script[src$="assets/skore/skore.js"]');
  const siteRoot = script.src.replace(/assets\/skore\/skore\.js$/, "");
  const siteUrl = (path) => new URL(path, siteRoot).href;

  const storage = {
    get(key) {
      try {
        return localStorage.getItem(key) === "true";
      } catch {
        return false;
      }
    },
    set(key, value) {
      try {
        localStorage.setItem(key, String(value));
      } catch {
        // file:// privacy settings may disable storage.
      }
    },
  };

  function topNavigation() {
    const items = window.__SKORE_NAV__;
    const header = document.querySelector(".md-header__inner");
    if (!Array.isArray(items) || !header || header.querySelector(".skore-topnav")) {
      return;
    }

    const nav = document.createElement("nav");
    nav.className = "skore-topnav";
    nav.setAttribute("aria-label", "Project");
    const current = location.href.split(/[?#]/)[0];

    const closeMenus = (except) => {
      nav.querySelectorAll(".skore-topnav__dropdown").forEach((dropdown) => {
        if (dropdown === except) return;
        dropdown.classList.remove("skore-topnav__dropdown--open");
        dropdown
          .querySelector(".skore-topnav__trigger")
          ?.setAttribute("aria-expanded", "false");
      });
    };

    items.forEach((item, index) => {
      if (!item.children) {
        const link = document.createElement("a");
        link.className = "skore-topnav__link";
        link.href = siteUrl(item.href);
        link.textContent = item.label;
        if (link.href === current) link.setAttribute("aria-current", "page");
        nav.append(link);
        return;
      }

      const dropdown = document.createElement("div");
      dropdown.className = "skore-topnav__dropdown";
      const trigger = document.createElement("button");
      const menu = document.createElement("div");
      const menuId = `skore-topnav-menu-${index}`;
      const caret = document.createElement("span");
      trigger.type = "button";
      trigger.className = "skore-topnav__trigger";
      caret.className = "skore-topnav__caret";
      caret.textContent = "▾";
      caret.setAttribute("aria-hidden", "true");
      trigger.append(item.label, caret);
      trigger.setAttribute("aria-haspopup", "menu");
      trigger.setAttribute("aria-expanded", "false");
      trigger.setAttribute("aria-controls", menuId);
      menu.id = menuId;
      menu.className = "skore-topnav__menu";
      menu.setAttribute("role", "menu");
      item.children.forEach((child) => {
        const link = document.createElement("a");
        link.className = "skore-topnav__menu-item";
        link.href = siteUrl(child.href);
        link.textContent = child.label;
        link.setAttribute("role", "menuitem");
        if (link.href === current) {
          link.setAttribute("aria-current", "page");
          trigger.classList.add("skore-topnav__trigger--active");
        }
        menu.append(link);
      });
      trigger.addEventListener("click", () => {
        const open = !dropdown.classList.contains("skore-topnav__dropdown--open");
        closeMenus(dropdown);
        dropdown.classList.toggle("skore-topnav__dropdown--open", open);
        trigger.setAttribute("aria-expanded", String(open));
      });
      dropdown.append(trigger, menu);
      nav.append(dropdown);
    });

    document.addEventListener("pointerdown", (event) => {
      if (!nav.contains(event.target)) closeMenus();
    });
    nav.addEventListener("keydown", (event) => {
      if (event.key !== "Escape") return;
      const trigger = nav.querySelector(
        ".skore-topnav__dropdown--open .skore-topnav__trigger",
      );
      closeMenus();
      trigger?.focus();
    });
    header.querySelector(".md-search")?.before(nav);
  }

  function pageContents() {
    document
      .querySelectorAll(".md-sidebar--secondary .md-nav__link")
      .forEach((link) => {
        if (link.querySelector(".skore-toc-label")) return;
        const label = document.createElement("span");
        label.className = "skore-toc-label";
        label.textContent = link.textContent.trim();
        link.title = label.textContent;
        link.replaceChildren(label);
      });
  }

  function tocButton() {
    const sidebar = document.querySelector(".md-sidebar--secondary");
    const inner = sidebar?.querySelector(".md-sidebar__inner");
    if (!sidebar || !inner || inner.querySelector("[data-skore-sidebar]")) return;
    sidebar.id = "skore-page-toc";

    const footer = document.createElement("div");
    footer.className = "skore-toc-footer";
    const button = document.createElement("button");
    button.type = "button";
    button.className = "skore-sidebar-toggle";
    button.dataset.skoreSidebar = "toc";
    button.setAttribute("aria-controls", sidebar.id);
    const icon = document.createElement("img");
    icon.className = "skore-sidebar-toggle__icon";
    icon.alt = "";
    icon.setAttribute("aria-hidden", "true");
    const label = document.createElement("span");
    label.className = "skore-sidebar-toggle__label";

    const update = (collapsed) => {
      document.body.classList.toggle("skore-toc-collapsed", collapsed);
      button.setAttribute("aria-expanded", String(!collapsed));
      button.setAttribute("aria-label", `${collapsed ? "Show" : "Hide"} contents`);
      icon.src = collapsed
        ? siteUrl("assets/skore/icons/square-caret-right-regular.svg")
        : siteUrl("assets/skore/icons/square-caret-left-regular.svg");
      label.textContent = collapsed ? "Show contents" : "Hide contents";
    };

    update(storage.get("skore-toc-collapsed"));
    button.addEventListener("click", () => {
      const collapsed = !document.body.classList.contains("skore-toc-collapsed");
      update(collapsed);
      storage.set("skore-toc-collapsed", collapsed);
    });
    button.append(icon, label);
    footer.append(button);
    inner.append(footer);
  }

  function initialize() {
    topNavigation();
    pageContents();
    tocButton();
    requestAnimationFrame(() =>
      document.body.classList.add("skore-motion-ready"),
    );
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", initialize);
  } else {
    initialize();
  }
})();
