import { extendTheme } from '@chakra-ui/react';

const theme = {
  fonts: {
    body: '"Exo 2", sans-serif',
    heading: '"Exo 2", serif'
  },
  colors: {
    warm : {
      1: '#ff7b00',
      2: '#ff9533',
      3: '#ffb066',
      4: '#ffca99'
    },
    cold: {
        1: '#0ac8e5',
        2: '#3bd3ea',
        3: '#6cdeef',
        4: '#9de9f5'
    }
  },
  styles: {
    global: {
      body: {
        fontSize: ['sm', null, null, 'md'],
        color: 'base.500',
        minHeight: '100vh'
      },
      '*': {
        lineHeight: 'calc(0.5rem + 1em)'
      }
    }
  }
};

export default extendTheme(theme);
