import unittest

from tools.inspire_mapping import (
    INSPIRE_JOINT_NAMES,
    LEFT_INSPIRE_JOINT_NAMES,
    RIGHT_INSPIRE_JOINT_NAMES,
    resolve_inspire_joint_indices,
)


class InspireMappingTest(unittest.TestCase):
    def test_runtime_order_is_resolved_by_name(self):
        runtime = list(reversed(INSPIRE_JOINT_NAMES)) + ["waist_yaw_joint"]
        indices = resolve_inspire_joint_indices(runtime)
        self.assertEqual(
            tuple(runtime[index] for index in indices), INSPIRE_JOINT_NAMES
        )
        self.assertEqual(len(RIGHT_INSPIRE_JOINT_NAMES), 6)
        self.assertEqual(len(LEFT_INSPIRE_JOINT_NAMES), 6)

    def test_missing_joint_fails(self):
        with self.assertRaises(ValueError):
            resolve_inspire_joint_indices(INSPIRE_JOINT_NAMES[:-1])

    def test_duplicate_joint_fails(self):
        with self.assertRaises(ValueError):
            resolve_inspire_joint_indices(INSPIRE_JOINT_NAMES + INSPIRE_JOINT_NAMES[:1])


if __name__ == "__main__":
    unittest.main()
