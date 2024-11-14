import React, { useEffect } from 'react';
import { createRoot } from 'react-dom/client';
import { ChakraProvider } from '@chakra-ui/react';
import { createBrowserRouter, RouterProvider } from 'react-router-dom';

import theme from '$styles/theme';

import PageLayout from '$components/common/page-layout';

const router = createBrowserRouter([
  {
    path: '/',
    element: <PageLayout />,
    children: [
      {
        index: true,
        // loader: requestLakes,
        lazy: () => import('$components/home')
      }
    ]
  }
]);

// Root component.
function Root() {
  useEffect(() => {
    // Hide the welcome banner.
    const banner = document.querySelector('#welcome-banner');
    if (!banner) return;
    banner.classList.add('dismissed');
    setTimeout(() => banner.remove(), 500);
  }, []);

  return (
    <ChakraProvider theme={theme} resetCSS>
      <RouterProvider router={router} />
    </ChakraProvider>
  );
}

const rootNode = document.querySelector('#app-container')!;
const root = createRoot(rootNode);
root.render(<Root />);
