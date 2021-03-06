#include "tts/goal.h"

namespace costar_task_plan {

  // Class to represent a physical set of end-effector positions.
  class InstantiatedTrajectory {
    using Ptr = std::shared_ptr<InstantiatedTrajectory>;
  };

  // Class to represent an abstract trajectory-generation policy.
  class Trajectory {
    using Ptr = std::shared_ptr<Trajectory>;

    // Convert a parameterized trajectory into a "real" trajectory.
    virtual InstantiatedTrajectory::Ptr instantiate() const = 0;
  };

}

