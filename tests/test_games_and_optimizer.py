"""
Unit Tests: Game Library Scanner & Optimizer Logic
"""

import unittest
from backend.games.library_scanner import GameLibraryScanner, GameEntry


class TestGamesAndOptimizer(unittest.TestCase):
    def test_game_library_scanner_presets(self):
        scanner = GameLibraryScanner()
        games = scanner.scan_all()
        self.assertGreater(len(games), 0)

        # Verify entry structure
        first_game = games[0]
        self.assertIsInstance(first_game, GameEntry)
        self.assertIsNotNone(first_game.name)
        self.assertIsNotNone(first_game.launch_command)
        self.assertTrue(first_game.use_dedicated_gpu)

    def test_prime_launch_command_construction(self):
        scanner = GameLibraryScanner()
        entry_dGPU = GameEntry(
            id="test_game",
            name="Cyberpunk 2077",
            launch_command="steam steam://rungameid/1091500",
            use_dedicated_gpu=True
        )
        cmd_dGPU = scanner.build_launch_command(entry_dGPU)
        self.assertIn("__NV_PRIME_RENDER_OFFLOAD=1", cmd_dGPU)
        self.assertIn("__GLX_VENDOR_LIBRARY_NAME=nvidia", cmd_dGPU)
        self.assertTrue(cmd_dGPU.endswith("steam steam://rungameid/1091500"))

        # When dedicated GPU is disabled
        entry_iGPU = GameEntry(
            id="test_game",
            name="Cyberpunk 2077",
            launch_command="steam steam://rungameid/1091500",
            use_dedicated_gpu=False
        )
        cmd_iGPU = scanner.build_launch_command(entry_iGPU)
        self.assertEqual(cmd_iGPU, "steam steam://rungameid/1091500")


if __name__ == "__main__":
    unittest.main()
