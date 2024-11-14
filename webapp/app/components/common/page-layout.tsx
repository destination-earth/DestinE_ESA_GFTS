import React from 'react';
import { Box, Flex } from '@chakra-ui/react';
import { Outlet } from 'react-router-dom';

export default function PageLayout() {
  
  return (
    <Flex direction='column' minHeight='100vh'>
      <Box as='main' flex='1'>
        <Outlet />
      </Box>
    </Flex>
  );
}
